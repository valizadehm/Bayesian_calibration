import sensivity_analysis
import os
import shutil
import numpy as np
from eppy.runner.run_functions import runIDFs
from eppy.modeleditor import IDF
from jinja2 import Environment, FileSystemLoader

class EplusPy:
    """Class Eppy in which methods are defined to run all the samples in E+ using eppy library"""

    def __init__(self, problem, X):
        self.problem = problem
        self.X = X
     

    def make_eplaunch_options(self, idf):
        """Make options for run, so that it runs like EPLaunch on Windows"""
        options = {
                            'ep_version': '9-4-0', # runIDFs needs the version number
                            'output_prefix':os.path.basename(idf.idfname).split('.')[0],
                            'output_suffix': 'D',
                            'output_directory': os.path.dirname(idf.idfname),
                            'readvars':True,
                            'expandobjects':True
                }
        return options

    def run_models(self, num_processors):
        """ 
            Run energyPlus models using variations based on self.X values
            param num_processors: number of processors
            return: -
        """

        idfs_list = []

        output_folder = os.path.join(os.path.abspath('./'), 'simulation\\real_time_results')
        # If the output directory exists, it is to delete the directory where the results of the previous run
        # had saved and then it is to create a new one
        if os.path.exists(output_folder) == True:
            shutil.rmtree(output_folder, ignore_errors = False)
        os.mkdir(output_folder)

        # Setting up the weather *.epw file 
        epw_path = os.path.join(os.path.abspath('./'), 'simulation\\FRA_NANTERRE_IWEC.epw')

        # Directories to idd file for running EnergyPlus
        idd_path = 'C:\\EnergyPlusV9-4-0\\Energy+.idd'
        # Setting idd file in IDF class
        IDF.setiddname(idd_path)        
        
        # Using Jinja2 templating to overwrite all the targeted parameters in the *.idf file
        environment = Environment(loader=FileSystemLoader(os.path.join(os.path.abspath('./'), 'simulation\\')))
        template = environment.get_template("NR3_V03-24_template.idf")
        
        
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
        runIDFs(runs, num_processors)




