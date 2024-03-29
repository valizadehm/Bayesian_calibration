import eppy_utility
import os
from time import time
import numpy as np
import pandas as pd
from abc import abstractmethod
from SALib.sample.sobol import sample
from SALib.analyze.sobol import analyze
from eppy.results import readhtml
from multiprocessing import Pool


class SenAna:
    """
        Class SenAna based on SALib documentation which defines all the attributes and methods 
        related to sensivity analysis using SALib
    """
    
    def __init__(self, parameters, num_initial_samples):

        """
            Constructor of the class to set problem parameter according to the documentation of SALib
            parameters: a dictionary type data structure containing uncertain parameters for the sensitivity analysis
                {"parameter name": [lower bound, upper bound]}
                problem = {
                    'num_vars': len(parameters),
                    'names': ['x1', 'x2', 'x3', ...],
                    'bounds': [[lower bound, upper bound],
                               [lower bound, upper bound],
                               [lower bound, upper bound],
                               ...
                              ],
                    'dists': ['unif', 'lognorm', 'triang', 'norm', 'truncnorm', ...]
                }
        """
        
        # Define the model inputs according the documentation of SALib
        self.num_initial_samples = num_initial_samples
        self.problem = {'num_vars': len(parameters['bounds']), 'names': parameters['obj_id'], 
                        'bounds': parameters['bounds'], 'dists': parameters['distributions']} 

        # Generate samples
        self.X = sample(self.problem, self.num_initial_samples)
        self.Y = np.zeros(self.X.shape[0])
        self.Si = None
      
    
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

    
    def read_results(self):
        """
            retrieve E+ outputs after simulation have been done
        """
    
        output_folder = os.path.join(os.path.abspath('./'), 'simulation\\real_time_results')
        
        for i in range(len(self.Y)):

            output_file = os.path.join(output_folder, 'run-{}-table.htm'.format(i))
            
            # Access to output summary table
            html_doc = open(output_file, 'r').read()  # file handle
            htables = readhtml.titletable(html_doc) # reads the tables with their titles
    
            # [table_index][0: table_title, 1: table_content][row_index][column_index]          
            # Time Not Comfortable Based on Simple ASHRAE 55-2004
            # self.Y[i] = htables[11][1][3][1]
            # Cooling
            # self.Y[i] = htables[3][1][2][1]
            # Heating
            # self.Y[i] = htables[3][1][1][1]
            # Energy Per Total Building Area [kWh/m2]
            # self.Y[i] = htables[0][1][2][2]
            # OccupantComfortDataSummaryMonthly_ For: PEOPLE RDC:TESLA
            self.Y[i] = htables[75][-1][14][4]

       
    
    def read_html_tables(self, filename):
        """
            read each html file and return the searched output in the summary report
        """
        html_doc = open(filename, 'r').read()  # file handle
        htables = readhtml.titletable(html_doc) # reads the tables with their titles
        # Heating
        return htables[3][1][1][1]
    
    
    def read_results_in_parallel(self, num_processors):
        """
            Profiting the parallel processing through Pool to read all the html summary reports
            first filling out a list of all the html files in a list and then share it by pool between processors
        """
        master_list = []
        # Getting the currently running script file (main.py)
        # file_dir = os.path.dirname(__file__)
        output_folder = os.path.join(os.path.abspath('./'), 'simulation\\real_time_results')
        for i in range(len(self.Y)):
            output_file = os.path.join(output_folder, 'run-{}-table.htm'.format(i))
            master_list.append(output_file)
   
        pool = Pool(processes=num_processors)
        self.Y = np.array(pool.map(self.read_html_tables, master_list))

    

    def evaluate(self, num_processors):
        """
            Perform analysis
            param Y: A Numpy array containing the model outputs of dtype=float
            return: A dictionary of sensitivity indices containing the following entries.
                - `Si` - the single effect of each parameter
                - `ST` - The total eefect of each parameter
                - `names` - the names of the parameters
        """

        # Inititiating an object from class Eppy to run the energyPlus models for all samples 
        # and obtain parameter Y
        eplus = eppy_utility.EplusPy(self.problem, self.X)
        
        start_time = time()
        eplus.run_models(num_processors)
        duration = time() - start_time
        print("§"*100)
        print("It took {} seconds ({} hours) to run all the {} E+ simulations.".format(duration, duration/3600,
                                                    2*self.num_initial_samples*(self.problem['num_vars'] + 1)))    
        print("§"*100)

        # read the output target in the all summary reports
        start_time = time()
        # self.read_results()
        self.read_results_in_parallel(num_processors)
     
        duration = time() - start_time
        print("It took {} seconds ({} hours) to read all the {} tables of" 
              " E+ model evaluations.".format(duration, duration/3600,
              2*self.num_initial_samples*(self.problem['num_vars'] + 1)))    
        print("§"*100)
        
        # Running the analysis phase which is the last one
        start_time = time()
        self.Si = analyze(self.problem, self.Y, print_to_console=True, parallel=True, 
                          keep_resamples=True, n_processors=num_processors, seed=2024) 
        
        duration = time() - start_time
        print("§"*100)
        print("It took {} seconds ({} hours) to conduct analysis of sensivity.".format(duration, duration/3600))   
        
        return self.Si




