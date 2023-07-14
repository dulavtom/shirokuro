#!/usr/bin/python3
from Solver import *
import fileinput


if __name__ == '__main__':
    for array in fileinput.input():
        array = array.replace('\n', '')
        solver = Solver(array)
        solution_array = solver.solve()
        print(solution_array)
