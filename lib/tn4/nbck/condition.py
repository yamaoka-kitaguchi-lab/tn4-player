from enum import Flag, auto


class Condition(Flag):
    DONTCARE = auto()
    IS       = auto()
    INCLUDE  = auto()
    INCLUDED = auto()
    EXCLUDE  = auto()


class ConditionalValue:
    def __init__(self, value=None, condition=Condition.DONTCARE):
        self.value     = value
        self.condition = condition
