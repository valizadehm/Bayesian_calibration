import os
import shutil
import numpy as np
from eppy.results.readhtml import titletable
from eppy.runner.run_functions import runIDFs
from eppy.modeleditor import IDF
from jinja2 import Environment, FileSystemLoader
from functools import partial
from multiprocessing import Pool


class EplusPy:
    
    """
    Class Eppy in which methods are defined to run all the samples in E+ using eppy library
    """
    def __init__(self, idd_file, epw_file, idf_template_file):
            
        # Setting all the necessary paths to run the model
        self.idd_file = idd_file
        self.epw_file = epw_file  
        self.idf_template_file = idf_template_file
        
        
    def make_eplaunch_options(self, idf):
        
        """
        Make options for run, so that it runs like EPLaunch on Windows
        """
        options = {'ep_version': '9-4-0', # runIDFs needs the version number
                   'output_prefix': os.path.basename(idf.idfname).split('.')[0],
                   'output_suffix': 'D',
                   'output_directory': os.path.dirname(idf.idfname),
                   'readvars': True,
                   'expandobjects': True}
        
        return options


    def get_idd_file(self):
        return self.idd_file
        
    
    def get_epw_file(self):
        return self.epw_file
    
    
    def get_idf_template_file(self):
        return self.idf_template_file
        
    
    def run_models(self, param_names, X, eval_folder, num_processors):
        
        """ 
        Run energyPlus models at each point of the sample X
        params_names: names of the parameters
        eval_folder: path to the folder that wil contain the model evaluations
        num_processors: number of processors
        """

        idfs_list = []
        
        # The following commands allow us to delete the outputs folder if it already exists and to create a new one at the same path
        if os.path.exists(eval_folder) == True:
            shutil.rmtree(eval_folder, ignore_errors = False)
        os.mkdir(eval_folder)

        # Setting idd files path in IDF class
        IDF.setiddname(self.get_idd_file())        
   
        # IDF template file
        idf_template_file = self.get_idf_template_file()
        environment = Environment(loader = FileSystemLoader(os.path.join(os.path.split(idf_template_file)[0], '')))
        template = environment.get_template(os.path.split(idf_template_file)[1])
        
        for i, values in enumerate(X):
            
            # Creation of a dictionary with the values to update in the *.idf files             
            param_dict = dict(zip(param_names, values))

            # Updating the parameters in the *.idf files
            filename = f"run-{i}.idf"
            idf_file = os.path.join(eval_folder, filename)
            content = template.render(param_dict)
                
            with open(idf_file, mode = "w", encoding = "utf-8") as idf:
                idf.write(content)
  
            idfs_list.append(idf_file)

        # Generator for generating idf objects of the class IDF
        idf_objects = (IDF(idf, self.get_epw_file()) for idf in idfs_list)
        runs = ((idf, self.make_eplaunch_options(idf)) for idf in idf_objects)

        #  Launching the simulations once all the *.idf files for each sample have been already created
        #  runIDFs needs the version number while idf.run does not need the second argument (options here)
        runIDFs(runs, num_processors)

    def read_html_tables(self, html_file, outputs_indices):
        
        """
        read a html file and return the searched output(s) in the summary report
        """
        
        # Get the number of output(s) to read in the file
        outputs_number = outputs_indices.shape[0]
        
        # Open the file in reading mode
        html_read = open(html_file, 'r').read()
        
        # Define the wanted output(s)
        Y = np.zeros(outputs_number)
        
        # Get the tables of the html file
        tables = titletable(html_read)
        
        # Get the output(s) from the html file
        for i in range(outputs_number):
            Y[i] = tables[int(outputs_indices[i,0])][1][int(outputs_indices[i,1])][int(outputs_indices[i,2])]
        
        return Y
    
    def read_Eplus_results(self, sample_size, eval_folder, outputs_indices, num_processors):
        
        """
        Profiting the parallel processing through Pool to read all the html summary reports
        first filling out a list of all the html files and then share it by pool between processors
        """
        
        # Get the list of all summary report files
        master_list = []
        for i in range(sample_size):
            master_list.append(os.path.join(eval_folder, 'run-{}-table.htm'.format(i)))
        
        # Initializing the parallelization
        pool = Pool(processes = num_processors)
        
        # Define a partial function on which apply the parallelization
        read_html = partial(self.read_html_tables, outputs_indices = outputs_indices)
        
        # Store the wanted output(s) after parallelization 
        Y = np.array(pool.map(read_html, master_list))
        
        return Y