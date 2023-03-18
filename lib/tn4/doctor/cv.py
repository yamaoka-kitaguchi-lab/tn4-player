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
        self.value     = self.__to_set(value)
        self.condition = condition
        self.priority  = priority


    def __to_set(self, value):
        if type(value) == list:
            return set(value)

        if type(value) in [bool, int, str]:
            return { value }

        if value is None:
            return set()

        return value


    def is_satisfied_by(self, value):
        value = self.__to_set(value)
        is_subset_of = lambda a, b: len(a - b) == 0
        is_independent_of = lambda a, b: len(a & b) == 0

        match self.condition:
            case Condition.DONTCARE:
                return True

            case Condition.IS:
                return self.value == value

            case Condition.INCLUDE:
                return is_subset_of(self.value, value)

            case Condition.INCLUDED:
                return is_subset_of(value, self.value)

            case Condition.EXCLUDE:
                return is_independent_of(self.value, value)

            case Condition.CONFLICT:
                return False


    def to_value(self, value, value_type=list):
        value = self.__to_set(value)
        rt = None

        if self.is_satisfied_by(value):
            rt = value

        match self.condition:
            case Condition.IS | Condition.INCLUDE:
                rt = self.value

            case Condition.INCLUDED:
                rt = value & self.value

            case Condition.EXCLUDE:
                rt = value - self.value

        if value_type == list:
            if len(rt) == 0:
                return None
            return list(rt)

        if value_type in [ bool, str, int ]:
            if len(rt) == 1:
                return list(rt)[0]
            return None

        return rt


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


    def dump(self):
        return {
            "Condition": self.condition,
            "Value":     self.value,
            "Priority":  self.priority,
        }

