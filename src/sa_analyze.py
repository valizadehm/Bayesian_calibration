import os
import numpy as np
from SALib.analyze.sobol import analyze
from eppy.results import readhtml

problem = {
    'num_vars': 9,
    'names': ['Leaf_Area_Index', 
              'Leaf_Reflectivity',
              'Leaf_Emissivity',
              'Albedo',
              'Infiltration',
              'Visible_Transmittance',
              'People_density',
              'Power_density',
              'Mechanical_ventilation'],
    'bounds': [[1.0, 5.0],
               [0.05, 0.4],
               [0.8, 1.0],
               [0.05, 1.0],
               [0.1, 0.8],
               [0.1, 0.9],
               [2.0, 25.0],
               [4.0, 12.0],
               [0.0, 0.0038]]
    }

Y = np.zeros(2560)

output_folder = 'D:\\Projet\\Thesis\\Simulations\\SensivityAnalysis\\real_time_results'
for k in range(2560):
    output_file = os.path.join(output_folder, 'run-{}-table.htm'.format(k))
    

    # Access to output summary table
    html_doc = open(output_file, 'r').read()
    htables = readhtml.titletable(html_doc) # reads the tables with their titles

    # heating
    Y[k] = htables[3][1][1][1]
    #total_site_energy_per_area
    #Y[k] = htables[0][1][2][1]


Si = analyze(problem, Y, print_to_console=True, parallel=True, keep_resamples=True, n_processors=16, seed=2024)