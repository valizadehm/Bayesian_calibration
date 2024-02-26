import eppy_utility
import os
import time
import numpy as np
from abc import abstractmethod
from SALib.sample.sobol import sample
from SALib.analyze.sobol import analyze
from eppy.results import readhtml


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
                              ]
                }
        """
        
        # Define the model inputs according the documentation of SALib
        self.num_initial_samples = num_initial_samples
        self.problem = {'num_vars': len(parameters['bounds']), 'names': parameters['obj_id'], 'bounds': parameters['bounds']} 

        # Generate samples
        self.X = sample(self.problem, self.num_initial_samples)
        self.Y = self.Y = np.zeros(self.X.shape[0])
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


    
    def reading_results(self):
        """retrieve E+ outputs after simulation have been done"""

        #file_dir = os.path.dirname(__file__)
        parent_dir = 'D:\\Projet\\Thesis\\Simulations\\SensivityAnalysis'
        output_folder = os.path.join(parent_dir, 'real_time_results')
        
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
    
    
    def evaluate(self, processors):
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
        
        start_time = time.time()
        eplus.run_models(processors)
        end_time = time.time()
        #****************************************************************************************************************
        print("It took {} seconds to run all the {} E+ simulations.".format((end_time - start_time), 
                                        2*self.num_initial_samples*(self.problem['num_vars'] + 1)))    
        #****************************************************************************************************************

        # read the output target in the all summary reports
        start_time = time.time()
        self.reading_results()
        end_time = time.time()
        #****************************************************************************************************************
        print("It took {} seconds to read all the {} E+ model evaluations.".format((end_time - start_time), 
                                               2*self.num_initial_samples*(self.problem['num_vars'] + 1)))    
        #****************************************************************************************************************
        
        # Running the analysis phase
        start_time = time.time()
        self.Si = analyze(self.problem, self.Y, print_to_console=True, parallel=True, 
                          keep_resamples=True, n_processors=processors, seed=2024)
        
        end_time = time.time()
        #****************************************************************************************************************
        print("It took {} seconds to conduct analysis of sensivity.".format((end_time - start_time)))   
        #****************************************************************************************************************
        
        return self.Si




