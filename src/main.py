import os
import time
import sensivity_analysis

def main():
    """main function"""

    # Get the total number of initial samples for Sobol Sensivity Analysis
    num_initial_samples = int(input("Enter the total number of samples as a multiplication of 2:"))
    start_time = time.time()

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
    
    #Instantiate an object from the class SALib
    sa = sensivity_analysis.SenAna(parameters, num_initial_samples)

    # Obtaining indeces of sensivity anlysis through Sobol method
    Si = sa.evaluate(processors = 16)
    end_time = time.time()
    #****************************************************************************************************************
    print("It took altogether {} seconds to conduct the whole sensivity analysis.".format((end_time - start_time)))    
    #****************************************************************************************************************

if __name__ == '__main__':
    main()