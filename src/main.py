import os
import shutil
from time import time
import sensivity_analysis

def main():
    """main function"""

    print("~"*100)
    # Getting the total number of initial samples for Sobol Sensivity Analysis
    num_initial_samples = int(input("Enter the total number of samples as a multiplication of 2:"))
    print("+"*100)

    start_time = time()

    # Parameters for sensivity analysis: bounds, the id of each object in EnergyPlus (these ids are used directly 
    # inside the idf template to be replaed and creat the idf samples) and their corresponding distribution function
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
                            [19, 0.25],
                            [26, 0.25],
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
                                  'unif', 'unif', 'unif', 'norm', 'norm', 'unif']
            }
    
    #Instantiate an object from the class SALib
    sa = sensivity_analysis.SenAna(parameters, num_initial_samples)

    # Obtaining indeces of sensivity anlysis through Sobol method
    Si = sa.evaluate(num_processors = 16)
    
    duration = time() - start_time
    print("§"*100)
    print("It took altogether {} seconds ({} hours) to conduct the whole "
          "sensivity analysis.".format(duration, duration/3600))    
    print("§"*100)

    # Saving the indices into first a data frame and then into a *.csv file
    total_Si, first_Si, second_Si = Si.to_df()
    
    output_folder = os.path.join(os.path.abspath('./simulation'), "n={} and p={}".format(num_initial_samples,
                                                                                  len(parameters['obj_id'])))
    if os.path.exists(output_folder) == True:
        shutil.rmtree(output_folder, ignore_errors = False)
    os.mkdir(output_folder)
    
    # Writing out the Si Sobol indices into csv files
    total_Si.to_csv(os.path.join(output_folder,"total_Si.csv"),  sep=',', index=False, encoding='utf-8')
    first_Si.to_csv(os.path.join(output_folder,"first_Si.csv"),  sep=',', index=False, encoding='utf-8')
    second_Si.to_csv(os.path.join(output_folder,"second_Si.csv"),sep=',', index=False, encoding='utf-8')


if __name__ == '__main__':
    main()