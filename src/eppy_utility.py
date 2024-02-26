import sensivity_analysis
import os
import shutil
import numpy as np
from eppy.runner.run_functions import runIDFs
from eppy.modeleditor import IDF
from eppy.results import readhtml
from jinja2 import Environment, FileSystemLoader

class EplusPy:
    """Class Eppy in which methods are defined to run all the samples in E+ using eppy library"""

    def __init__(self, problem, X):
        self.problem = problem
        self.X = X
        self.Y = np.zeros(self.X.shape[0])
     

    def make_eplaunch_options(self, idf):
        """Make options for run, so that it runs like EPLaunch on Windows"""
        #idfversion = idf.idfobjects['version'][0].Version_Identifier.split('.')
        #idfversion.extend([0] * (3 - len(idfversion)))
        #idfversionstr = '-'.join([str(item) for item in idfversion])
        options = {
                            'ep_version': '9-4-0', # runIDFs needs the version number
                            'output_prefix':os.path.basename(idf.idfname).split('.')[0],
                            'output_suffix': 'D',
                            'output_directory': os.path.dirname(idf.idfname),
                            'readvars':True,
                            'expandobjects':True
                }
        return options

    def run_models(self, processors):
        """ 
            Run energyPlus models using variations based on self.X values
            param num_processors: number of processors
            return: -
        """

        idfs_list = []

        #file_dir = os.path.dirname(__file__)
        file_dir = 'D:\\Projet\\Thesis\\Simulations\\SensivityAnalysis'
        output_folder = os.path.join(file_dir, 'real_time_results')
        # removing directory where the results of the previous run are saved
        shutil.rmtree(output_folder, ignore_errors = False)
        os.mkdir(output_folder)

        # Setting up the weather *.epw file 
        folder_parent = 'D:\\Projet\\Thesis\\Simulations'
        epw_file = 'EnergyPlus\\2024\\fevrier2024\\FRA_NANTERRE_IWEC.epw'
        epw_path = os.path.abspath(os.path.join(folder_parent, epw_file))

        # Directories to idd file for running EnergyPlus
        idd_path = 'C:\\EnergyPlusV9-4-0\\Energy+.idd'
        #idd_path = os.path.abspath(os.path.join(folder_parent, idd_file))
        # Setting idd file in IDF class
        IDF.setiddname(idd_path)        
        
        # Using Jinja2 templating to overwrite all the targeted parameters in the *.idf file
        environment = Environment(loader=FileSystemLoader("D:\\Projet\\Thesis\\Simulations\\SensivityAnalysis\\"))
        template = environment.get_template("NR3_V02-24_template.idf")
        
        
        for i, values in enumerate(self.X):
            # making dictionary of all parameters which are substituted in the original idf file
            parameters_dic = {}
            for j in range(self.problem['num_vars']):
                parameters_dic[self.problem['names'][j]] = values[j]

            
            filename = f"run-{i}.idf"
            content = template.render(parameters_dic)
            with open(os.path.join(output_folder, filename), mode="w", encoding="utf-8") as sampled_idf:
                sampled_idf.write(content)

            idf_path = os.path.join(output_folder, f"run-{i}.idf")
  
            idfs_list.append(idf_path)

        # Generator for generating idf objects of the class IDF
        idf_objects = (IDF(idf, epw_path) for idf in idfs_list)
        runs = ((idf, self.make_eplaunch_options(idf)) for idf in idf_objects)

        #  Launching the simulations once all the *.idf files for each sample have been already created
        #  runIDFs needs the version number while idf.run does not need the above arg
        runIDFs(runs, processors)

    
    def reading_results(self):
        """retrieve E+ outputs after simulation have been done"""

        #file_dir = os.path.dirname(__file__)
        file_dir = 'D:\\Projet\\Thesis\\Simulations\\SensivityAnalysis'
        output_folder = os.path.join(file_dir, 'real_time_results')
        
        for i in range(len(self.Y)):

            output_file = os.path.join(output_folder, 'run-{}-table.htm'.format(i))
            
            # Access to output summary table
            html_doc = open(output_file, 'r').read()
            htables = readhtml.titletable(html_doc) # reads the tables with their titles
    
            # [table_index][0: table_title, 1: table_content][row_index][column_index]
            # heating
            # self.Y[i] = htables[3][1][1][1]
            #total_site_energy_per_area
            self.Y[i] = htables[0][1][2][1]

        return self.Y



