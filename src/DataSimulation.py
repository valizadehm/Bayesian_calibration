# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 16:01:37 2024

@author: Cesi
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import EppyUtility

def main():
    
    from SALib.sample.latin import sample as lhs
    from SALib.sample.sobol import sample as sbl
    import math
    import numpy as np
    import pandas as pd
    
    # *.idd file for EnergyPlus
    idd_file = "C:/EnergyPlusV9-4-0/Energy+.idd"
    
    # Folder with the final results
    results_folder = "C:/Users/Cesi/Documents/CalibrationMediumOffice/Boulder/Simulations"
    
    # Parameters file
    parameters_file = "C:/Users/Cesi/Documents/CalibrationMediumOffice/Boulder/Simulations/SelectedParameters.csv"
    df_params = pd.read_csv(parameters_file, header = None)
    
    # Define the parameters that will be studied using a *.csv file
    names = df_params.iloc[:,0].to_list()
    bounds = np.reshape(df_params.iloc[:,1].to_list()+df_params.iloc[:,2].to_list(), (2, len(names))).T.tolist()
    dist = df_params.iloc[:,3].to_list()
            
    # SALib problem to launch LHS simulations
    problem = {'num_vars': len(names), 'names': names, 
                    'bounds': bounds, 'dists': dist}
    
    # Seed to use
    seed = 2024
    
    # Year(s) for which generate the observations
    years = input("Year(s) for which generate the *.epw file(s): ").split()
    years = list(map(int, years))
    
    # Months of the year
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    
    # Sapmling method
    method = input("LHS (1) or Sobol (0) sampling method: ")
    
    if method != 0:
        
        # Number of points to simulate for each month of each year
        N = int(input("Size of the sample for each month of each year: "))
        
        # Total number of points to simulate
        sample_size = N*len(months)*len(years)
        
        # Sample the points
        X = lhs(problem, sample_size, seed)
        
    else:
        
        # Number of points to simulate for each month of each year
        N = int(input("Size of the sample for each month of each year (will be the nearest power of two): "))
        
        # Total number of points to simulate
        sample_size = 2**math.ceil(math.log(N, 2))*len(months)*len(years)
        
        # Sample the points
        X = sbl(problem, sample_size, seed)
        
    
    # Save the sample X
    X_df = pd.DataFrame(data = X, columns = problem["names"], index = [f"Y{i}M{j}S{k}" for  i in years for j in range(1, len(months)+1) for k in range(1, N+1)])
    
    with open(os.path.join(results_folder, 'Samples.csv'), "w") as csv_file:
        X_df.to_csv(csv_file, index = True)
        
    X = X.reshape((len(years), len(months), N, len(names)))
    
    # Number of processes to run simultaneously
    num_processors = 8
      
    for i in range(len(years)):
        
        # Files to use to run EnergyPlus
        epw_file = f"C:/Users/Cesi/Documents/CalibrationMediumOffice/Boulder/USA_CO_Denver-Intl-AP.725650_AMY_{years[i]}.epw"
        idf_file = f"C:/Users/Cesi/Documents//CalibrationMediumOffice/Boulder/Simulations/MediumOfficeIDFMonthly-{years[i]}-SelPar.idf"
        eval_folder = os.path.join(results_folder, f"Evaluations{years[i]}")  
        
        # Instance of EplusPy class
        Eplus = EppyUtility.EplusPy(idd_file, epw_file, idf_file)
        
        # Array that will contain the outputs
        Y = np.zeros((N, len(months)))
        
        for j in range(len(months)):
        
            # Run the model
            Eplus.run_models(names, X[i,j], eval_folder, num_processors) 
            
            # Indice for monthly electricity consumption in our idf configuration
            output_indice = np.array([[0, j+1, 1]])
            
            # Get the output
            Y[:, j] = Eplus.read_Eplus_results(N, eval_folder, output_indice, num_processors).ravel()
    
        # Save the results in a *.csv file
        df = pd.DataFrame(Y, columns = months)
        with open(os.path.join(results_folder, f"SimulationData-{years[i]}.csv"), "w") as csv_file:
            df.to_csv(csv_file, index = False)   


if __name__ == '__main__':
    main()