import os
import numpy as np
from SALib.sample.sobol import sample
from SALib.analyze.morris import analyze
from eppy.runner import run_functions
from eppy.modeleditor import IDF
from eppy.results import readhtml

# Define the model inputs
"""
    problem = {
        'num_vars': 3,
        'names': ['x1', 'x2', 'x3'],
        'bounds': [[-3.14159265359, 3.14159265359],
                [-3.14159265359, 3.14159265359],
                [-3.14159265359, 3.14159265359]]
    }
"""


# Generate samples
"""
    param_values = sample(problem, 1024)
"""


# Perform analysis
"""
    Si = analyze(problem, Y, print_to_console=True)
"""
