# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 10:33:48 2024

@author: Cesi
"""

def main():
    
    import pandas as pd
    import numpy as np
    import os
    
    # Folder with the final results
    results_folder = "C:/Users/Cesi/Documents/CalibrationMediumOffice/Boulder/Observations"
    
    # Year(s) for which generate the observations
    years = input("Year(s) for which generate the *.epw file(s): ").split()
    years = list(map(int, years))
    
    # Months for which generate the observations
    months = input("Months for which generate the *.epw file(s): ").split()
    months = list(map(int, months))
    if len(months) == 1:
        months = [months[0] for i in range(len(years))]
    
    # Columns that contain the wanted data
    col_indices = input("Column indices of the wanted data columns: ").split()
    col_indices = list(map(int, col_indices))
    
    # Extract and save wanted data for each selected year
    for i in range(len(years)):
        
        # The first 8 lines of the *.epw file are information, not data
        # They need to be removed before execution
        epw_file = f"C:/Users/Cesi/Documents/CalibrationMediumOffice/Boulder/Observations/EPW_{years[i]}.epw"
        df_epw = pd.read_csv(epw_file, header = None)
        
        # Extract wanted data
        data = df_epw.iloc[:,col_indices]
        
        # Days number for each month
        days = [31,28,31,30,31,30,31,31,30,31,30,31]
            
        # Check if it is a leap year to possibly change the number of days for february
        if years[i]%4 == 0 and years[i]%4000 != 0 or years[i]%400 == 0:
            days[1] = 29
            
        # Cumulative sum of all days multiplied by 24 to get all hours
        days.insert(0, 0)
        cs_days = np.cumsum(days)*24
            
        avg_data = np.zeros((months[i], len(col_indices)))
        for j in range(months[i]):
            avg_data[j,:] = data.iloc[cs_days[j]:cs_days[j+1],:].mean()
        avg_data = pd.DataFrame(avg_data)
        
        # Save wanted data
        with open(os.path.join(results_folder, f"ObservedDataAvg-{years[i]}.csv"), "w") as file:
            avg_data.to_csv(file, index = False, header = False)

if __name__ == '__main__':
    main()