
class Literal:

    def __init__(self, position, var, positivity=True):
        """
        :param position: position of the item in the puzzle
        :param var: logic variable - state of the item
        :param positivity: is the var positive or negative?
        """
        self.position = position
        self.var = var
        self.positivity = positivity

    def __str__(self):
        text = ""
        text += "[{0} {1} {2}]".format("+" if self.positivity else '-', self.position,  self.var)
        return text

    def flip(self):
        self.positivity = not self.positivity
        return self

    def __repr__(self):
        return str(self)