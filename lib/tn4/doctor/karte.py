from enum import Flag, auto

from tn4.doctor.cv import ConditionalValue
from tn4.helper.utils import flatten


class Annotation:
    def __init__(self, message, severity=1):
        self.severity = severity
        self.message  = message


    def dump(self):
        return {
            "Severity": self.severity,
            "Message": self.message,
        }


class InterfaceCondition:
    def __init__(self, argument, manual_repair=False):
        self.argument            = argument
        self.manual_repair       = manual_repair  # if true, nbck skips repairing but just present messages

        self.remove_from_nb      = ConditionalValue()
        self.is_enabled          = ConditionalValue()
        self.description         = ConditionalValue()
        self.tags                = ConditionalValue()
        self.is_tagged_vlan_mode = ConditionalValue()
        self.tagged_vids         = ConditionalValue()
        self.untagged_vid        = ConditionalValue()


    def __add__(self, other):
        argument      = flatten([self.argument, other.argument])  # concatinate as list
        manual_repair = self.manual_repair | other.manual_repair

        condition = InterfaceCondition(argument, manual_repair)
        condition.remove_from_nb      = self.remove_from_nb + other.remove_from_nb
        condition.is_enabled          = self.is_enabled + other.is_enabled
        condition.description         = self.description + other.description
        condition.tags                = self.tags + other.tags
        condition.is_tagged_vlan_mode = self.is_tagged_vlan_mode + other.is_tagged_vlan_mode
        condition.tagged_vids         = self.tagged_vids + other.tagged_vids
        condition.untagged_vid        = self.untagged_vid + other.untagged_vid

        return condition


    def __radd__(self, other):
        return self.__add__(other)


class Category(Flag):
    WARN   = auto()
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()


class Assessment:
    def __init__(self, category, keys=[], current=None, desired=None, arguments=[], annotations=[]):
        self.category      = category
        self.keys          = keys
        self.current_state = current
        self.desired_state = desired
        self.arguments     = arguments
        self.annotations   = annotations


    def dump(self):
        d = {
            "Category":    self.category,
            "Arguments":   self.arguments,
            "Annotations": [ v.dump() for v in self.annotations ],
        }

        if self.current_state is not None:
            d |= {
                "Current": self.current_state.dump()
            }

        if self.desired_state is not None:
            d |= {
                "Desired": self.desired_state.dump()
            }

        return d


class KarteType(Flag):
    DEVICE    = auto()
    INTERFACE = auto()
    UNDEFINED = auto()


class Karte:
    def __init__(self, karte_type=KarteType.UNDEFINED):
        self.type = karte_type
        self.all  = {}


    def add(self, assessment):
        v = self.all
        for i, k in enumerate(assessment.keys):
            if k not in v:
                v[k] = {} if i < len(assessment.keys)-1 else []
            v = v[k]

        v.append(assessment)


    def dump(self):
        v = {}

        for hostname in self.all:
            v[hostname] = {}

            if type(self.all[hostname]) != dict:
                assess = self.all[hostname][0]
                v[hostname] = assess.dump()

            else:
                for ifname in self.all[hostname]:
                    assess = self.all[hostname][ifname][0]
                    v[hostname][ifname] = assess.dump()

        return v

