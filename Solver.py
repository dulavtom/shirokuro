import numpy as np
from config import *
from Literal import *
import pycosat


class Solver:

    def __init__(self, array):
        # the input array representing definition of the problem
        self.array = array
        # the puzzle has rectangular shape, the size is a size of the side of the rectangle
        self.size = int(np.sqrt(len(self.array)))
        # this is a node out of the puzzle, and it represents an invalid option
        self.trash_node = self.size * self.size

    def coordToFlat(self, coords):
        """
        Transform coords in 2D array into index in corresponding 1D array. Each coord outside the puzzle will return
        the thrash tile.
        :param coords:
        :return:
        """
        if type(coords) is not tuple:
            return coords

        (x, y) = coords
        if min(x, y) < 0 or max(x, y) >= self.size:
            return self.trash_node
        return y * self.size + x

    def flatToCoord(self, position):
        """
        Transform index in 1D array into coords in corresponding 2D array
        :param position:
        :return:
        """
        y = position // self.size
        x = position - y * self.size
        return x, y

    def add_clause(self, clause):
        """
        Transform given clause from symbolic representation into DIMACS representation
        :param clause: disjunction of literals we want to transform
        :return:
        """
        clause_dimacs = []
        for literal in clause:
            position = self.coordToFlat(literal.position)
            sign = 1 if literal.positivity else -1
            literal_dimacs = sign*(1 + position * num_vars + vars[literal.var])
            clause_dimacs.append(literal_dimacs)
        return clause_dimacs

    def clause_to_str(self, clause):
        """
        Convert clause from DIMACS representation back into symbolic representation
        :param clause:
        :return:
        """
        signs = [True if x > 0 else False for x in clause]
        # Variables starts from 0, but 0 cant have negative value, thus DIMACS starts from 1, and I have to
        # subtract this offset
        clause = [abs(x)-1 for x in clause]
        indices = [self.flatToCoord(x//num_vars) for x in clause]

        variables = [x % num_vars for x in clause]
        variables = [vars_rev[x] for x in variables]
        condition = [Literal(index, var, sign) for sign, index, var in zip(signs, indices, variables)]
        return condition

    def __at_least_one(self, item, list_of_var):
        """
        Create only one clause - disjunction of all literals
        :param item: tile affected by variables
        :param list_of_var:
        :return:
        """
        formula = [[Literal(item, x, True) for x in list_of_var]]
        return formula

    def __at_most_one(self, item, list_of_var):
        """
        It creates a => ! b for all (a, b) in list_of_var
        :param item:
        :param list_of_var:
        :return:
        """
        formula = []
        for i in range(len(list_of_var) - 1):
            for j in range(i + 1, len(list_of_var)):
                clause = [Literal(item, list_of_var[i], False), Literal(item, list_of_var[j], False)]
                formula.append(clause)
        return formula

    def XOR(self, item, list_of_var):
        """
        Exactly one variable from list holds for the tile
        :param item:
        :param list_of_var:
        :return:
        """
        formula = []
        formula.extend(self.__at_least_one(item, list_of_var))
        formula.extend(self.__at_most_one(item, list_of_var))
        return formula

    def NAND(self, item, list_of_var):
        """
        None of the variables from the list holds for the tile. It might seem it is a disjunction of negative literals,
        but note that each literal has brackets around itself i.e [[l1], ... [ln]] thus it is actually set of clauses
        :param item:
        :param list_of_var:
        :return:
        """

        formula = [[Literal(item, x, False)] for x in list_of_var]
        return formula

    def OR(self, item, list_of_var):
        """
        Basically at_least_one condition
        :param item:
        :param list_of_var:
        :return:
        """
        return self.__at_least_one(item, list_of_var)

    def implication(self, conditions, consequences):
        """
        The following form is assumed: AND [conditions] => AND [ OR [consequences]]
        :param conditions:
        :param consequences:
        :return:
        """
        clause = [x.flip() for x in conditions]
        formula = [x + clause for x in consequences]
        return formula

    def ray_cast(self, coord, dir):
        """
        For a given node and direction return the color of the first head it sees in te direction,
        in a case that no head is present in the way, return None
        :param coord:
        :param dir:
        :return:
        """
        target = tuple(np.array(coord) + directions[dir])
        if self.coordToFlat(target) == self.trash_node:
            return None
        if self.array[self.coordToFlat(target)] == 'b':
            return "BLACK"
        elif self.array[self.coordToFlat(target)] == 'w':
            return "WHITE"
        else:
            return self.ray_cast(target, dir)

    def generate_formula(self):
        """
        Generate all conditions to solve our problem. Here is the heart of the logic of the solver
        :return:
        """
        formula = []

        # generate general clauses (works always no matter how the particular puzzle looks like)
        for i in range(0, self.size):
            for j in range(0, self.size):
                item = (i, j)
                left = (i-1, j)
                right = (i+1, j)
                up = (i, j-1)
                down = (i, j+1)
                # each tile is either HEAD or is FREE
                formula.extend(self.XOR(item, ["HEAD", "FREE"]))

                # if a tile is FREE, then it has exactly one ORIENTATION and has no DIRECTION
                formula.extend(self.implication([Literal(item, "FREE")], self.XOR(item, ["VERTICAL", "HORIZONTAL", "EMPTY"])))
                formula.extend(self.implication([Literal(item, "FREE")], self.NAND(item, ["NORTH", "SOUTH", "EAST", "WEST"])))
                # if a tile is HORIZONTAL (thus is FREE), then left (right) neighbor is either HORIZONTAL or EAST (WEST)
                formula.extend(self.implication([Literal(item, "HORIZONTAL")], self.OR(left, ["HORIZONTAL", "EAST"])))
                formula.extend(self.implication([Literal(item, "HORIZONTAL")], self.OR(right, ["HORIZONTAL", "WEST"])))
                # if a tile is VERTICAL (thus is FREE), then up (down) neighbor is either VERTICAL or SOUTH (NORTH)
                formula.extend(self.implication([Literal(item, "VERTICAL")], self.OR(up, ["VERTICAL", "SOUTH"])))
                formula.extend(self.implication([Literal(item, "VERTICAL")], self.OR(down, ["VERTICAL", "NORTH"])))

                # if a tile is HEAD, then it has exactly one DIRECTION and has no ORIENTATION
                formula.extend(self.implication([Literal(item, "HEAD")], self.XOR(item, ["NORTH", "SOUTH", "EAST", "WEST"])))
                formula.extend(self.implication([Literal(item, "HEAD")], self.NAND(item, ["VERTICAL", "HORIZONTAL", "EMPTY"])))
                # if a tile is EAST (thus is HEAD), then the right neighbor is either HORIZONTAL or WEST
                formula.extend(self.implication([Literal(item, "EAST")], self.OR(right, ["HORIZONTAL", "WEST"])))
                # if a tile is WEST (thus is HEAD), then the left neighbor is either HORIZONTAL or EAST
                formula.extend(self.implication([Literal(item, "WEST")], self.OR(left, ["HORIZONTAL", "EAST"])))
                # if a tile is NORTH (thus is HEAD), then the up neighbor is either VERTICAL or SOUTH
                formula.extend(self.implication([Literal(item, "NORTH")], self.OR(up, ["VERTICAL", "SOUTH"])))
                # if a tile is SOUTH (thus is HEAD), then the down neighbor is either VERTICAL or NORTH
                formula.extend(self.implication([Literal(item, "SOUTH")], self.OR(down, ["VERTICAL", "NORTH"])))

        # generate clauses determined by particular puzzle
        for i in range(0, self.size):
            for j in range(0, self.size):
                item = (i, j)
                # Determine whether tile is a head or is free
                if self.array[self.coordToFlat(item)] == "0":
                    formula.extend(self.OR(item, ["FREE"]))
                else:
                    formula.extend(self.OR(item, ["HEAD"]))

                # Now generate conditions that ensures connection between black heads and white heads.
                # It works as follows: the black head can be directed only in a direction when it can see white head.
                valid_directions = []
                if self.array[self.coordToFlat(item)] == "b":
                    for dir in directions:
                        if self.ray_cast(item, dir) == "WHITE":
                            valid_directions.append(Literal(item, dir))
                if len(valid_directions):
                    formula.append(valid_directions)

        # thrash node represents invalid option, thus is False in all variables
        formula.extend(self.NAND(self.flatToCoord(self.trash_node), ["HEAD", "FREE",
                                                                     "NORTH", "EAST", "SOUTH", "WEST",
                                                                     "VERTICAL", "HORIZONTAL", "EMPTY",
                                                                     "WHITE", "BLACK"]))

        return formula

    def formula_into_CNF(self, formula):
        """
        Transform formula from symbolic to DIMACS representation
        :param formula:
        :return:
        """
        CNF = []
        for x in formula:
            CNF.append(self.add_clause(x))
        return CNF

    def CNF_into_formula(self, CNF):
        """
        Transform formula from DIMACS to symbolic representation
        :param CNF:
        :return:
        """
        formula = []
        for clause in CNF:
            print(clause)
            formula.append(self.clause_to_str(clause))
        return formula

    def extract_solution(self, solution):
        """
        From a solver we get positivity/negativity of each variable.
        From that we want to find out solution to the problem
        :param solution:
        :return:
        """
        array = ["X"] * self.trash_node
        for tile in range(self.trash_node):
            offset = tile * num_vars

            if solution[offset + vars["HEAD"]] > 0:
                if solution[offset + vars["EAST"]] > 0:
                    array[tile] = "E"
                elif solution[offset + vars["WEST"]] > 0:
                    array[tile] = "W"
                elif solution[offset + vars["NORTH"]] > 0:
                    array[tile] = "N"
                elif solution[offset + vars["SOUTH"]] > 0:
                    array[tile] = "S"
                else:
                    raise Exception("The tile {0} is a HEAD with no direction".format(self.flatToCoord(tile)))
            elif solution[offset + vars["FREE"]] > 0:
                if solution[offset + vars["HORIZONTAL"]] > 0:
                    array[tile] = "H"
                elif solution[offset + vars["VERTICAL"]] > 0:
                    array[tile] = "V"
                elif solution[offset + vars["EMPTY"]] > 0:
                    array[tile] = "0"
                else:
                    raise Exception("The tile {0} is FREE with no orientation".format(self.flatToCoord(tile)))
            else:
                raise Exception("The tile {0} is not a HEAD neither FREE".format(self.flatToCoord(tile)))

        return array

    def solve(self):
        """
        Return the solution of the problem
        :return:
        """
        formula = self.generate_formula()
        CNF = self.formula_into_CNF(formula)
        solution = pycosat.solve(CNF)
        if solution == "UNSAT":
            return 'X'
        solution_array = self.extract_solution(solution)
        # convert list of chars into string
        solution_array = "".join(solution_array)
        return solution_array

