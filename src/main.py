import os
from time import time
import sensivity_analysis

def main():
    """main function"""

    print("~"*90)
    # Getting the total number of initial samples for Sobol Sensivity Analysis
    num_initial_samples = int(input("Enter the total number of samples as a multiplication of 2:"))
    print("+"*90)

    start_time = time()

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
                            [0.0, 0.0038],
                            [18, 20],
                            [24, 26],
                            [3, 5]
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
                            'Mechanical_ventilation',
                            'Heating_setpoint',
                            'Cooling_setpoint',
                            'Lighting_density'
                        ],
                'distributions': ['unif', 'unif', 'unif', 'unif', 'unif', 'unif',
                                  'unif', 'unif', 'unif', 'unif', 'unif', 'unif']
            }
    
    #Instantiate an object from the class SALib
    sa = sensivity_analysis.SenAna(parameters, num_initial_samples)

    # Obtaining indeces of sensivity anlysis through Sobol method
    Si = sa.evaluate(processors = 16)
    
    duration = time() - start_time
    print("§"*90)
    print("It took altogether {} seconds ({} hours) to conduct the whole sensivity analysis.".format(duration, duration/3600))    
    print("§"*90)

    # Saving the indices into first a data frame and then into a *.csv file
    total_Si, first_Si, second_Si = Si.to_df()
    # Writing out all the indices of Sobol sensivity analysis
    output_folder = r'D:\Projet\Thesis\Simulations\SensivityAnalysis\saved_results'
    total_Si.to_csv(os.path.join(output_folder,"n={}\\total_Si.csv".format(num_initial_samples)),  sep=',', index=False, encoding='utf-8')
    first_Si.to_csv(os.path.join(output_folder,"n={}\\first_Si.csv".format(num_initial_samples)),  sep=',', index=False, encoding='utf-8')
    second_Si.to_csv(os.path.join(output_folder,"n={}\\second_Si.csv".format(num_initial_samples)),sep=',', index=False, encoding='utf-8')


if __name__ == '__main__':
    main()