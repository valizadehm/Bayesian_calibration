import os
import shutil
import time
import numpy as np
from abc import abstractmethod
from SALib.sample.sobol import sample
from SALib.analyze.sobol import analyze
from eppy.runner.run_functions import runIDFs
from eppy.modeleditor import IDF
from eppy.results import readhtml
from idf_functions import EppyUtilityIdf
from jinja2 import Environment, FileSystemLoader


class SobolBes:
    """Constructor of the class"""
    def __init__(self, parameters, num_initial_samples):

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
        self.num_initial_samples = num_initial_samples
        self.problem = {'num_vars': len(parameters['bounds']), 'names': [], 'bounds': []}
        self.problem['bounds'] = parameters['bounds']
        self.problem['names'] = parameters['obj_id']        

        # Generate samples
        self.X = sample(self.problem, self.num_initial_samples)
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

    def get_names(self):
        """
            return: a list containing the names of parameters
            that will be screened for their sensitivity
        """
        return self.problem['names']


    @abstractmethod
    def run_models(self, num_processors):
        """
            Run model
            run energyPlus models using variations based on self.X values and 
            set self.Y values based on output of the simulations
            param idf:  energyPlus idf object
            param num_processors: number of processors
            return: -
        """
        pass


    def evaluate(self):
        """
            Perform analysis
            param Y: A Numpy array containing the model outputs of dtype=float
            return: A dictionary of sensitivity indices containing the following entries.
                - `Si` - the single effect of each parameter
                - `ST` - The total eefect of each parameter
                - `names` - the names of the parameters
        """
        if self.Y is None:
            raise NameError('Y, evaluate is not defined. Run E+ models first')
        self.Si = analyze(self.problem, self.Y, print_to_console=True)
        return self.Si

    
    
class SobolEppy(SobolBes):
    """Class Sobol in which methods are defined to run all the samples in E+ using eppy library"""
    
    def make_eplaunch_options(self, idf):
        """Make options for run, so that it runs like EPLaunch on Windows"""
        idfversion = idf.idfobjects['version'][0].Version_Identifier.split('.')
        idfversion.extend([0] * (3 - len(idfversion)))
        idfversionstr = '-'.join([str(item) for item in idfversion])
        options = {
                            'ep_version': '9-4-0', # runIDFs needs the version number
                            'output_prefix':os.path.basename(idf.idfname).split('.')[0],
                            'output_suffix': 'C',
                            'output_directory': os.path.dirname(idf.idfname),
                            'readvars':True,
                            'expandobjects':True
                }
        return options

    # Concret definition of the abstract method run_models()
    def run_models(self, processors):
        #if self.idf is None:
        #    raise TypeError('idf file has NOT  been set')
        #utility = EppyUtilityIdf()
        idfs_list = []

        #file_dir = os.path.dirname(__file__)
        file_dir = 'C:\\Simulations\\SensivityAnalysis'
        output_folder = os.path.join(file_dir, 'SA_results')
        # removing directory where the results of the previous run are saved
        shutil.rmtree(output_folder, ignore_errors = False)
        os.mkdir(output_folder)

        folder_parent = 'D:\\Projet\\Thesis\\Simulations'
        epw_file = 'EnergyPlus\\2024\\fevrier2024\\FRA_NANTERRE_IWEC.epw'
        epw_path = os.path.abspath(os.path.join(folder_parent, epw_file))

        # Using Jinja2 templating to overwrite all the targeted parameters in the *.idf file
        environment = Environment(loader=FileSystemLoader("D:\\Projet\\Thesis\\Simulations\\\SensivityAnalysis\\"))
        template = environment.get_template("NR3_V02-24_template.idf")
        
        
        for i, values in enumerate(self.X):
            # making dictionary of all parameters which are substituted in the original idf file
            parameters_dic = {}
            for j in range(self.problem['num_vars']):
                parameters_dic[self.problem['names'][j]] = values[j]

            
            filename = f"run-{i}.idf"
            content = template.render(parameters_dic)
            #path = r'D:\Projet\Thesis\Simulations\SensivityAnalysis'
            with open(os.path.join(output_folder, filename), mode="w", encoding="utf-8") as sampled_idf:
                sampled_idf.write(content)

            idf_path = os.path.join(output_folder, f"run-{i}.idf")
  
            idfs_list.append(idf_path)

        # Generator for generating idf objects of the class IDF
        idf_objects = (IDF(idf, epw_path) for idf in idfs_list)
        runs = ((idf, self.make_eplaunch_options(idf)) for idf in idf_objects)

        # runIDFs needs the version number while idf.run does not need the above arg
        runIDFs(runs, processors)

        # retrieve E+ outputs after simulation have been done
        num_samples = self.X.shape[0]
        self.Y = np.zeros(num_samples)


        for k in range(num_samples):
            output_file = os.path.join(output_folder, 'run-{}Table.htm'.format(k))
            
            #with open(output_file, "r", encoding='ISO-8859-1') as f:
            #    results_table = readhtml.titletable(f.read)
            html_doc = open(output_file, 'r').read()
            htables = readhtml.titletable(html_doc) # reads the tables with their titles

            #total_site_energy = utility.get_output(htables, ['Site and Source Energy', 'Total Site Energy'])
            #total_site_energy_per_area = total_site_energy[1]
            total_site_energy_per_area = htables[0][1][2][1]
            self.Y[k] = total_site_energy_per_area


def main():
    # Get the total number of initial samples for Sobol Sensivity Analysis
    num_initial_samples = int(input("Enter the total number of samples as a multiplication of 2:"))
    start_time = time.time()

    # Directories to idd file for running EnergyPlus
    idd_path = 'C:\\EnergyPlusV9-4-0\\Energy+.idd'
    #idd_path = os.path.abspath(os.path.join(folder_parent, idd_file))

    # Parameters for sensivity analysis: bounds, the id of each object in EnergyPlus and 
    # the number of parameters
    parameters = {
                'bounds': [
                            [1.0, 5.0],
                            [0.05, 0.4],              
                            [0.8, 1.0],
                            [0.05, 1.0],
                            [0.1, 0.8],
                            [0.1, 0.9],
                            [2.0, 25.0],
                            [4.0, 12.0],
                            [0.0, 0.0038]
                    ],
                'obj_id': [
                            'Leaf_Area_Index',
                            'Leaf_Reflectivity',
                            'Leaf_Emissivity',
                            'Albedo',
                            'Infiltration',
                            'Visible_Transmittance',
                            'People_density',
                            'Power_density',
                            'Mechanical_ventilation'
                        ]
            }
    
    #Instantiate an object from the class SobolEppy
    sobol = SobolEppy(parameters, num_initial_samples)

    # Setting idd file in IDF class
    IDF.setiddname(idd_path)

    #Launching the simulations once all the idf files for each sample have been already created
    sobol.run_models(processors = 16)

    #Sensivity anlysis through Sobol method
    Si = sobol.evaluate()

    end_time = time.time()
    #**************************************************************************************************
    print("It took {} seconds to run the code with {} samples.".format((start_time - end_time), num_initial_samples))    
    #**************************************************************************************************
if __name__ == '__main__':
    main()
