from enum import Flag, auto
from functools import reduce
import operator


class Condition(Flag):
    DONTCARE  = auto()
    IS        = auto()
    INCLUDE   = auto()
    INCLUDED  = auto()
    EXCLUDE   = auto()
    CONFLICT  = auto()


class ConditionalValue:
    def __init__(self, value=None, condition=Condition.DONTCARE):
        self.value     = value
        self.condition = condition


    def __add__(self, other):
        is_subset_of = lambda a, b: len(a - b) > 0
        is_independent_of = lambda a, b: len(a & b) == 0

        self.condition == Condition.DONTCARE and return other

        ## IS-IS

        if self.condition == Condition.IS and other.condition == IS:
            if self.value == other.value:
                return ConditionalValue(other.value, other.condition)

        ## IS-INCLUDE

        if self.condition == Condition.IS and other.condition == Condition.INCLUDE:
            if is_subset_of(other.value, self.value):
                return ConditionalValue(self.value, self.condition)

        if other.condition == Condition.IS and self.condition == Condition.INCLUDE:
            if is_subset_of(self.value, other.value):
                return ConditionalValue(other.value, other.condition)

        ## IS-INCLUDED

        if self.condition == Condition.IS and other.condition == Condition.INCLUDED:
            if is_subset_of(self.value, other.value):
                return ConditionalValue(self.value, self.condition)

        if other.condition == Condition.IS and self.condition == Condition.INCLUDED:
            if is_subset_of(other.value, self.value):
                return ConditionalValue(other.value, other.condition)

        ## IS-EXCLUDE

        if self.condition == Condition.IS and other.condition == Condition.EXCLUDE:
            if is_independent_of(self.value, other.value):
                return ConditionalValue(self.value, self.condition)

        if other.condition == Condition.IS and self.condition == Condition.EXCLUDE:
            if is_independent_of(other.value, self.value):
                return ConditionalValue(other.value, other.condition)

        ## INCLUDE-INCLUDE

        if self.condition == Condition.INCLUDE and other.condition == Condition.INCLUDE:
            v = self.value | other.value
            return ConditionalValue(v, Condition.INCLUDE)

        ## INCLUDE-INCLUDED

        if self.condition == Condition.INCLUDE and other.condition == Condition.INCLUDED:
            if is_subset_of(other.value, self.value):
                return ConditionalValue(self.value, self.condition)

        if other.condition == Condition.INCLUDE and self.condition == Condition.INCLUDED:
            if is_subset_of(self.value, other.value):
                return ConditionalValue(other.value, other.condition)

        ## INCLUDE-EXCLUDE

        ## INCLUDED-INCLUDED

        ## INCLUDED-EXCLUDE

        ## EXCLUDE-EXCLUDE







        return ConditionalValue(None, condition.CONFLICT)





