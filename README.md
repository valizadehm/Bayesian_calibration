# Bayesian_calibration

# Bayesian calibration

Before anything, if we want to run a sensivity analysis using Sobol method, we need to orient toward directory where the source codes and virtual environment `.venv` and `(..\Bayesian_calibration\src)` are found. Then we should activate virtual environmment through either *Git Bash* or *ms command line* or *Powershell*. I personnally use *Git Bash* command as below:
```
source .venv/Scripts/activate
```
When *(venv)* appears at the beginning of the directory.
The structure tree of the code follow as:

```
src
|   Bayesian.yaml
|   CalibrationPyMC.ipynb
|   DataSimulation.py
|   EppyUtility.py
|   eppy_utility.py
|   ExtractDataEPW.py
|   main.py
|   Metamodel_GP.ipynb
|   Predictions.py
|   sensivity_analysis.py
|
+---.ipynb_checkpoints
|
\---__pycache__
```
Open `main.py` file where we define ll the parameters of the energy model for sensivity analysis.
Sensivity Analysis is carried out usign Sobol method and we are asked to enter $n$ to determin the total number of samples by $2n(p+1)$ formula where $n$ is a number of the form $2^x$ as the numerical algorithm necessits it and $p$ is the number of parameters of sensivity analysis.

Short after, the code starts the generation of $2n(p+1)$ samples and execution of all the samples through Eppy module defined in `eppy_utimity.py` file where we define the directories towards weather file and template `NR3_template.idf` file for running EnergyPlus in parallel mode. Once the EnergyPlus evaluation of all codes finishes, it starts reading the target output variable specified in `sensivity_analysis.py` file.

In the `simulation` folder, one finds `NR3_template.idf` file which should be edit as a template file for the parameters of calibration with the same name as their definition in `main.py` file.