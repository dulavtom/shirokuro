import numpy as np

vars = {"HEAD": 0, "FREE": 1,
        "NORTH": 2, "EAST": 3, "SOUTH": 4, "WEST": 5,
        "VERTICAL": 6, "HORIZONTAL": 7, "EMPTY": 8,
        "WHITE": 9, "BLACK": 10}
num_vars = len(vars)
vars_rev = {value: key for key, value in vars.items()}
directions = {"NORTH": np.array([0, -1]), "EAST": np.array([1, 0]), "SOUTH": np.array([0, 1]),
              "WEST": np.array([-1, 0])}