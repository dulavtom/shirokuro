#!/usr/bin/python3
from Solver import *
import fileinput


if __name__ == '__main__':
    for array in fileinput.input():
        array = array.replace('\n', '')
        solver = Solver(array)
        solution_array = solver.solve()

        # print(array)
        print(solution_array)
        # print(solver.ray_cast((4, 5), "SOUTH"))
        # print(solver.ray_cast((1, 1), "NORTH"))

        # if solution_array == 'X':
        #     print('X')
        # else:
        #     for i in range(solver.size):
        #         print(solution_array[i*solver.size:(i+1)*solver.size])
