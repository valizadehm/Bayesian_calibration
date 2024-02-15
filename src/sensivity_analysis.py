import os
import shutil
import numpy as np
from abc import abstractmethod
from SALib.sample.sobol import sample
from SALib.analyze.sobol import analyze
from eppy.runner.run_functions import runIDFs
from eppy.modeleditor import IDF
from eppy.results import readhtml
from idf_functions import EppyUtilityIdf


class SobolBes:
    
    def __init__(self, parameters):

        """
            parameters: a dictionary type data structure containing uncertain parameters for the sensitivity analysis
                {"parameter name": [lower bound, upper bound]}
                problem = {
                    'num_vars': len(parameters),
                    'names': ['x1', 'x2', 'x3', ...],
                    'bounds': [[lower bound, upper bound],
                               [lower bound, upper bound],
                               [lower bound, upper bound],
                               ...
                              ]
                }
        """
        
        # Define the model inputs
        self.idf = None
        self.problem = {'num_vars': len(parameters['bounds']), 'names': [], 'bounds': []}
        self.problem['bounds'] = parameters['bounds']
        self.objects = parameters['obj_id']
        
        for obj in self.objects:
            self.problem['names'].append(obj[0])
        """
        for key, value in parameters:
            self.problem['names'].append(key)
            self.problem['bounds'].append(value)
        """
     

        # Generate samples
        self.X = sample(self.problem, 1050)
        self.Y = None
        self.Si = None
        
    @abstractmethod
    def set_idf(self, idf_path, epw_path, idd_path):
        pass   
        
    
    def get_samples(self):
        """
            return: a numpy.ndarray containing the model inputs required for method of Sobol.
        """
        return self.X

    def get_idf(self):
        """
            return: an idf object to launch energyPlus through eppy
        """

    def get_names(self):
        """
            return: a list containing the names of parameters
            that will be screened for their sensitivity
        """
        return self.problem['names']


    # Run model
    @abstractmethod
    def run_models(self, num_processors):
        """
            run enrgyPlus models using variations based on self.X values and 
            set self.Y values based on output of the simulations
            param idf:  energyPlus idf object
            param num_processors: number of processors
            return:
        """
        pass


    # Perform analysis
    def evaluate(self):
        """
            param Y: A Numpy array containing the model outputs of dtype=float
            return: A dictionary of sensitivity indices containing the following entries.
                - `mu` - the mean elementary effect
                - `mu_star` - the absolute of the mean elementary effect
                - `sigma` - the standard deviation of the elementary effect
                - `mu_star_conf` - the bootstrapped confidence interval
                - `names` - the names of the parameters
        """
        if self.Y is None:
            raise NameError('Y, evaluate is not defined. Run E+ models first')
        self.si = analyze(self.problem, self.Y, print_to_console=True)
        return self.si
    
    
class SobolEppy(SobolBes):

    # Concret definition of the abstract method set_idf()
    def set_idf(self, idf_path, epw_path, idd_path):
        # Setting idd file in IDF class
        IDF.setiddname(idd_path)
        # Instantiate an object from the class IDF with the original idf file
        self.idf = IDF(idf_path, epw_path)

    # Concret definition of the abstract method run_models()
    def run_models(self, processors):
        if self.idf is None:
            raise TypeError('idf file has NOT  been set')
        utility = EppyUtilityIdf()
        idf_list = []
        #file_dir = os.path.dirname(__file__)
        file_dir = 'D:\Projet\Thesis\Simulations\SensivityAnalysis'
        output_folder = os.path.join(file_dir, 'SA_results')
        # removing directory where the results of the previous run are saved
        shutil.rmtree(output_folder, ignore_errors = False)
        os.mkdir(output_folder)

        for i, values in enumerate(self.X):   #each sample
            idf_temp = utility.copy(self.idf)
            for j, value in enumerate(values):
                for obj in self.objects[j]:
                    if len(obj.split(',')) == 3:
                        obj_id, obj_name, field = obj.split(',')
                    else:
                        obj_id, field = obj.split(',')
                        obj_name = None
                    utility.idf_handle(idf_temp, obj_id, obj_name, field, value)
            idf_temp.idfabsname = os.path.join(output_folder, 'run-{}.idf'.format(i))
            idf_temp.save()

            # Make options for run, so that it runs like EPLaunch on Windows
            # idfversion = idf_temp.idfobjects['version'][0].Version_Identifier.split('.')
            # idfversion.extend([0] * (3 - len(idfversion)))
            # idfversionstr = '-'.join([str(item) for item in idfversion])
            options = {
                        'ep_version': '9-4-0', # runIDFs needs the version number
                        'output_prefix': 'run-{}'.format(i),
                        'output_suffix': 'C',
                        'output_directory': os.path.dirname(idf_temp.idfabsname),
                        'readvars':True,
                        'expandobjects':True
                }
            idf_list.append([idf_temp, options])

        # runIDFs needs the version number while idf.run does not need the above arg
        runIDFs(idf_list, processors)
        # retrieve E+ outputs after simulation have been done
        num_samples = self.X.shape[0]
        self.Y = np.zeros(num_samples)


        for k in range(num_samples):
            output_file = os.path.join(output_folder, 'run-{}Table.htm'.format(k))
            
            #with open(output_file, "r", encoding='ISO-8859-1') as f:
            #    results_table = readhtml.titletable(f.read)
            html_doc = open(output_file, 'r').read()
            htables = readhtml.titletable(html_doc) # reads the tables with their titles

            total_site_energy = utility.get_output(htables, ['Site and Source Energy', 'Total Site Energy'])
            total_site_energy_per_area = total_site_energy[1]
            self.Y[k] = total_site_energy_per_area




def main():
    # Directories to idf, idd, epw files for running EnergyPlus
    folder_parent = 'D:\\Projet\\Thesis\\Simulations'
    #idd_file = 'EnergyPlus\\2024\\fevrier\\Energy+.idd'
    idf_file = 'EnergyPlus\\2024\\fevrier\\NR3_V02-24.idf'
    epw_file = 'EnergyPlus\\2024\\fevrier\\FRA_NANTERRE_IWEC.epw'

    idd_path = 'C:\\EnergyPlusV9-4-0\\Energy+.idd'
    #idd_path = os.path.abspath(os.path.join(folder_parent, idd_file))
    idf_path = os.path.abspath(os.path.join(folder_parent, idf_file))
    epw_path = os.path.abspath(os.path.join(folder_parent, epw_file))

    # Parameters for sensivity analysis: bounds, the id of each object in EnergyPlus and the number of parameters
    parameters = {
                    'bounds': [
                                [1.0, 5.0],
                                [0.05, 0.5],              
                                [0.8, 1.0],
                                [0.05, 1.0],
                                [0.1, 0.8],
                                [0.1, 0.9],
                                [2.0, 25.0],
                                [4.0, 12.0],
                                [0.0, 0.0038]
                        ],
                    'obj_id': [
                                ['Material:RoofVegetation,NR3 - Vegetation_.15,Leaf_Area_Index'],
                                ['Material:RoofVegetation,NR3 - Vegetation_.15,Leaf_Reflectivity'],
                                ['Material:RoofVegetation,NR3 - Vegetation_.15,Leaf_Emissivity'],
                                ['GroundHeatTransfer:Slab:Materials,ALBEDO_Surface_Albedo_No_Snow',
                                 'GroundHeatTransfer:Basement:SurfaceProps,ALBEDO_Surface_albedo_for_No_snow_conditions'],
                                ['ZoneInfiltration:DesignFlowRate,RDC:HALLRDC Infiltration,Air_Changes_per_Hour',
                                 'ZoneInfiltration:DesignFlowRate,RDC:TESLA Infiltration,Air_Changes_per_Hour',
                                 'ZoneInfiltration:DesignFlowRate,RDC:LUMIERE Infiltration,Air_Changes_per_Hour',
                                 'ZoneInfiltration:DesignFlowRate,Etage:NOBEL Infiltration,Air_Changes_per_Hour',
                                 'ZoneInfiltration:DesignFlowRate,Etage:TURING Infiltration,Air_Changes_per_Hour'],
                                ['WindowMaterial:Glazing,1225,Visible_Transmittance_at_Normal_Incidence',
                                 'WindowMaterial:Glazing,7776,Visible_Transmittance_at_Normal_Incidence',
                                 'WindowMaterial:Glazing,7968,Visible_Transmittance_at_Normal_Incidence',
                                 'WindowMaterial:Glazing,7985,Visible_Transmittance_at_Normal_Incidence'],
                                ['People,People RDC:TESLA,People_per_Zone_Floor_Area',
                                 'People,People RDC:LUMIERE,People_per_Zone_Floor_Area',
                                 'People,People Etage:NOBEL,People_per_Zone_Floor_Area',
                                 'People,People Etage:TURING,People_per_Zone_Floor_Area'],
                                ['OtherEquipment,RDC:LOCALTECH Miscellaneous gain,Power_per_Zone_Floor_Area',
                                 'OtherEquipment,RDC:TESLA Miscellaneous gain,Power_per_Zone_Floor_Area',
                                 'OtherEquipment,RDC:LUMIERE Miscellaneous gain,Power_per_Zone_Floor_Area',
                                 'OtherEquipment,Etage:LOCALSERVEURS Miscellaneous gain,Power_per_Zone_Floor_Area',
                                 'OtherEquipment,Etage:NOBEL Miscellaneous gain,Power_per_Zone_Floor_Area',
                                 'OtherEquipment,Etage:TURING Miscellaneous gain,Power_per_Zone_Floor_Area'],
                                ['DesignSpecification:OutdoorAir,RDC:TESLA Design Specification Outdoor Air Object,Outdoor_Air_Flow_per_Zone_Floor_Area',
                                 'DesignSpecification:OutdoorAir,RDC:LUMIERE Design Specification Outdoor Air Object,Outdoor_Air_Flow_per_Zone_Floor_Area',
                                 'DesignSpecification:OutdoorAir,Etage:NOBEL Design Specification Outdoor Air Object,Outdoor_Air_Flow_per_Zone_Floor_Area',
                                 'DesignSpecification:OutdoorAir,Etage:TURING Design Specification Outdoor Air Object,Outdoor_Air_Flow_per_Zone_Floor_Area']
                            ]
                }
    
    # Instantiate an object from the class SobolEppy
    sobol = SobolEppy(parameters)
    sobol.set_idf(idf_path, epw_path, idd_path)

    # Launching the simulations once all the idf files for each sample have been already created
    sobol.run_models(processors = 8)

    # Sensivity anlysis through Sobol method
    Si = sobol.evaluate()

if __name__ == '__main__':
    main()
