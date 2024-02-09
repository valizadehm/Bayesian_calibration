import os
import shutil
import numpy as np
from abc import abstractmethod
from SALib.sample.sobol import sample
from SALib.analyze.morris import analyze
from eppy.runner import run_functions
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
        self.problem = {'num_vars': len(parameters), 'names': [], 'bounds': []}
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
        self.X = sample(self.problem, 1024)
        self.Y = None
        self.si = None
        
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
        self.si = analyze(self.problem, self.X, self.Y)
        return self.si
    
    
class SobolEppy(SobolBes):

    # Concret definition of the abstract method set_idf()
    def set_idf(self, idf_path, epw_path, idd_path):
        IDF.setiddname(idd_path)
        self.idf = IDF(idf_path, epw_path)

    # Concret definition of the abstract method run_models()
    def run_models(self, processors):
        if self.idf is None:
            raise TypeError('idf file has NOT  been set')
        utility = EppyUtilityIdf
        idf_list = []
        file_dir = os.path.dirname(__file__)
        output_folder = os.path.join(file_dir, 'SA_results')
        try:
            shutil.rmtree(output_folder)
        except FileNotFoundError as err:
            print(err)
        os.mkdir(output_folder)

        for i, values in enumerate(self.X):   #each sample
            idf_temp = utility.copy(self.idf)
            for j, value in enumerate(values):
                for obj in self.objects[j]:
                    obj_id, obj_name, field = obj.split(',')
                    utility.idf_handle(idf_temp, obj_id, obj_name, field, value)
            idf_temp.idfname = os.path.join(output_folder, 'run-{}.idf'.format(i))
            idf_temp.save()

            sim_settings = {'EnergyPlus_version': '9.4.0', 
                            'verbose': 'q', 
                            'output_directory': output_folder,
                            'readvars': True,
                            'output_prefix': "run-{}-".format(i)}
            idf_list.append([idf_temp, sim_settings])

        
        run_functions.runIDFs(idf_list, processors=processors)
        # retrieve E+ outputs after simulation have been done
        num_samples = self.X.shape[0]
        self.Y = np.zeros(num_samples)


        for k in range(num_samples):
            output_file = os.path.join(output_folder, 'run-{}-table.htm'.format(k))
            with open(output_file, "r", encoding='ISO-8859-1') as f:
                results_table = readhtml.titletable(f.read)

        total_site_energy = utility.get_output(results_table, ['Site and Source Energy', 'Total Site Energy'])
        total_site_energy_per_area = total_site_energy[1]
        self.Y[k] = total_site_energy_per_area



# Directories to idf, idd, epw files for running EnergyPlus
folder_parent = 'D:\Projet\Thesis\Simulations'
idf_file = 'EnergyPlus\\2024\\fevrier\\NR3_V02-24.idf'
idd_file = 'C:\EnergyPlusV9-4-0\Energy+.idd'
epw_file = 'EnergyPlus\\2024\\fevrier\\NR3_NANTERRE_IWEC.epw'

idf_path = os.path.abspath(os.path.join(folder_parent, idf_file))
epw_path = os.path.abspath(os.path.join(folder_parent, epw_file))

# Parameters for sensivity analysis: bounds, the id of each object in EnergyPlus and the number of parameters
parameters = {'bounds': [[0.05, 0.5],
                         [1.0, 5.0],
                         [0.8, 1.0],
                         [0.05, 1.0],
                         [0.1, 0.8],
                         [0.1, 0.9],
                         [2.0, 25.0 ],
                         [4.0, 12.0 ],
                         [0.0, 0.0038]],
              'obj_id': [
                         ['Material:RoofVegetation,NR3 - Vegetation_.15,Leaf Area Index'],
                         ['Material:RoofVegetation,NR3 - Vegetation_.15,Leaf Reflectivity'],
                         ['Material:RoofVegetation,NR3 - Vegetation_.15,Leaf Emissivity'],
                         ['GroundHeatTransfer:Slab:Materials,ALBEDO: Surface Albedo: No Snow',
                          'GroundHeatTransfer:Basement:SurfaceProps,ALBEDO: Surface albedo for No snow conditions'],
                         ['ZoneInfiltration:DesignFlowRate,RDC:HALLRDC Infiltration,Air Changes per Hour',
                          'ZoneInfiltration:DesignFlowRate,RDC:TESLA Infiltration,Air Changes per Hour',
                          'ZoneInfiltration:DesignFlowRate,RDC:LUMIERE Infiltration,Air Changes per Hour',
                          'ZoneInfiltration:DesignFlowRate,Etage:NOBEL Infiltration,Air Changes per Hour',
                          'ZoneInfiltration:DesignFlowRate,Etage:TURING Infiltration,Air Changes per Hour'],
                         ['WindowMaterial:Glazing,1225,Visible Transmittance at Normal Incidence',
                          'WindowMaterial:Glazing,7776,Visible Transmittance at Normal Incidence',
                          'WindowMaterial:Glazing,7968,Visible Transmittance at Normal Incidence',
                          'WindowMaterial:Glazing,7985,Visible Transmittance at Normal Incidence'],
                         ['People,People RDC:HALLRDC,People per Zone Floor Area',
                          'People,People RDC:TESLA,People per Zone Floor Area',
                          'People,People RDC:LUMIERE,People per Zone Floor Area',
                          'People,People RDC:LUMIERE,People per Zone Floor Area',
                          'People,People Etage:NOBEL,People per Zone Floor Area',
                          'People,People Etage:TURING,People per Zone Floor Area'],
                         ['OtherEquipment,RDC:LOCALTECH Miscellaneous gain,People per Zone Floor Area',
                          'OtherEquipment,RDC:TESLA Miscellaneous gain,People per Zone Floor Area',
                          'OtherEquipment,RDC:LUMIERE Miscellaneous gain,People per Zone Floor Area',
                          'OtherEquipment,Etage:LOCALSERVEURS Miscellaneous gain,People per Zone Floor Area',
                          'OtherEquipment,Etage:NOBEL Miscellaneous gain,People per Zone Floor Area',
                          'OtherEquipment,Etage:TURING Miscellaneous gain,People per Zone Floor Area'],
                         ['DesignSpecification:OutdoorAir,RDC:TESLA Design Specification Outdoor Air Object,Outdoor Air Flow per Zone Floor Area',
                          'DesignSpecification:OutdoorAir,RDC:LUMIERE Design Specification Outdoor Air Object,Outdoor Air Flow per Zone Floor Area',
                          'DesignSpecification:OutdoorAir,RDC:TESLA Design Specification Outdoor Air Object,Outdoor Air Flow per Zone Floor Area',
                          'DesignSpecification:OutdoorAir,Etage:NOBEL Design Specification Outdoor Air Object,Outdoor Air Flow per Zone Floor Area',
                          'DesignSpecification:OutdoorAir,Etage:TURING Design Specification Outdoor Air Object,Outdoor Air Flow per Zone Floor Area']
                        ]
            }
            

# Setting idd file in IDF class
IDF.setiddname(idd_file)

# Instantiate an object from the class IDF
idf_eppy = IDF(idf_path, epw_path)

sobol = SobolEppy(parameters)
sobol.set_idf(idf_path, epw_path, idd_file)

sobol.run_models(processors = 4)
si = sobol.evaluate()