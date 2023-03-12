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
    def __init__(self, value=None, condition=Condition.DONTCARE, priority=0):
        self.value     = value
        self.condition = condition
        self.priority  = priority

        if type(value) == list:
            self.value = set(value)
        if type(value) in [bool, int, str]:
            self.value = { value }


    def __add__(self, other):
        is_subset_of = lambda a, b: len(a - b) == 0
        is_independent_of = lambda a, b: len(a & b) == 0

        ## DONTCARE

        if self.condition == Condition.DONTCARE:
            return ConditionalValue(other.value, other.condition)

        if other.condition == Condition.DONTCARE:
            return ConditionalValue(self.value, self.condition)

        ## IS-IS

        if self.condition == Condition.IS and other.condition == Condition.IS:
            if self.value == other.value or self.value != other.value and self.priority > other.priority:
                return ConditionalValue(other.value, Condition.IS)
            elif self.value != other.value and self.priority < other.priority:
                return ConditionalValue(self.value, Condition.IS)

        ## IS-INCLUDE

        if self.condition == Condition.IS and other.condition == Condition.INCLUDE:
            if is_subset_of(other.value, self.value):
                return ConditionalValue(self.value, Condition.IS)

        if other.condition == Condition.IS and self.condition == Condition.INCLUDE:
            if is_subset_of(self.value, other.value):
                return ConditionalValue(other.value, Condition.IS)

        ## IS-INCLUDED

        if self.condition == Condition.IS and other.condition == Condition.INCLUDED:
            if is_subset_of(self.value, other.value):
                return ConditionalValue(self.value, Condition.IS)

        if other.condition == Condition.IS and self.condition == Condition.INCLUDED:
            if is_subset_of(other.value, self.value):
                return ConditionalValue(other.value, Condition.IS)

        ## IS-EXCLUDE

        if self.condition == Condition.IS and other.condition == Condition.EXCLUDE:
            if is_independent_of(self.value, other.value):
                return ConditionalValue(self.value, Condition.IS)
            elif self.priority > other.priority:
                v = self.value - other.value
                return ConditionalValue(v, Condition.IS)

        if other.condition == Condition.IS and self.condition == Condition.EXCLUDE:
            if is_independent_of(other.value, self.value):
                return ConditionalValue(other.value, Condition.IS)
            elif other.priority > self.priority:
                v = other.value - self.value
                return ConditionalValue(v, Condition.IS)

        ## INCLUDE-INCLUDE

        if self.condition == Condition.INCLUDE and other.condition == Condition.INCLUDE:
            v = self.value | other.value
            return ConditionalValue(v, Condition.INCLUDE)

        ## INCLUDE-INCLUDED

        if self.condition == Condition.INCLUDE and other.condition == Condition.INCLUDED:
            if is_subset_of(self.value, other.value):
                return ConditionalValue(self.value, Condition.INCLUDE)

        if other.condition == Condition.INCLUDE and self.condition == Condition.INCLUDED:
            if is_subset_of(other.value, self.value):
                return ConditionalValue(other.value, Condition.INCLUDE)

        ## INCLUDE-EXCLUDE

        if self.condition == Condition.INCLUDE and other.condition == Condition.EXCLUDE:
            if is_independent_of(other.value, self.value):
                return ConditionalValue(self.value, Condition.INCLUDE)

        if other.condition == Condition.INCLUDE and self.condition == Condition.EXCLUDE:
            if is_independent_of(self.value, other.value):
                return ConditionalValue(other.value, Condition.INCLUDE)

        ## INCLUDED-INCLUDED

        if self.condition == Condition.INCLUDED and other.condition == Condition.INCLUDED:
            v = self.value | other.value
            return ConditionalValue(v, Condition.INCLUDED)

        ## INCLUDED-EXCLUDE

        if self.condition == Condition.INCLUDED and other.condition == Condition.EXCLUDE:
            v = self.value - other.value
            return ConditionalValue(v, Condition.INCLUDED)

        if other.condition == Condition.INCLUDED and self.condition == Condition.EXCLUDE:
            v = other.value - self.value
            return ConditionalValue(v, Condition.INCLUDED)

        ## EXCLUDE-EXCLUDE

        if self.condition == Condition.EXCLUDE and other.condition == Condition.EXCLUDE:
            v = self.value | other.value
            return ConditionalValue(v, Condition.EXCLUDE)

        return ConditionalValue(None, Condition.CONFLICT)

    def __radd__(self, other):
        return self.__add__(other)
