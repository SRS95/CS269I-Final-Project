# CS269I-Final-Project
Implementation portion of the paper "A Game-Theoretic Analysis of Kaggle" by Sam Schwager, John Solitario, and Sam Sklar. 

To run V1Simulation, simply run the following from the command line:
```
python V1Simulation.py
```

To run with plotting such that the plots are saved in the plots directory, run:
```
python V1Simulation.py --plot --save
```
Or:
```
python V1Simulation.py -p -s
```
Note that the --save or -s argument can be omitted.

To download all dependencies, run:
```
pip install -r requirements.txt
```
Finally, to reproduce our results for finding the optimal number of users retained in the gold competition, run:
```
python V1Simulation.py -p -s -f
```
