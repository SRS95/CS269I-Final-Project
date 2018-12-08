# CS269I-Final-Project
Analyzing Kaggle from a game-theoretic standpoint.

To run V1Simulation, simply run the following from the command line:
```
python3 V1Simulation.py
```

To run with plotting such that the plots are saved in the plots directory, run:
```
python3 V1Simulation.py --plot --save
```
Or:
```
python3 V1Simulation.py -p -s
```
Note that the --save or -s argument can be omitted.

To download all dependencies, run:
```
pip3 install -r requirements.txt
```
Finally, to reproduce our results for finding the optimal number of users retained in the gold competition, run:
```
python3 V1Simulation.py -p -s -f
```
