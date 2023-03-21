from collections import OrderedDict
from enum import Flag, auto

from tn4.doctor.cv import ConditionalValue
from tn4.helper.utils import flatten


class InterfaceCondition:
    def __init__(self, argument, manual_repair=False):
        self.argument       = argument
        self.manual_repair  = manual_repair  # if true, nbck skips repairing but just present messages

        self.remove_from_nb = ConditionalValue()
        self.is_enabled     = ConditionalValue()
        self.description    = ConditionalValue()
        self.tags           = ConditionalValue()
        self.interface_mode = ConditionalValue()
        self.tagged_oids    = ConditionalValue()
        self.untagged_oid   = ConditionalValue()


    def __add__(self, other):
        argument      = flatten([self.argument, other.argument])  # concatinate as list
        manual_repair = self.manual_repair | other.manual_repair

        condition = InterfaceCondition(argument, manual_repair)
        condition.remove_from_nb = self.remove_from_nb + other.remove_from_nb
        condition.is_enabled     = self.is_enabled + other.is_enabled
        condition.description    = self.description + other.description
        condition.tags           = self.tags + other.tags
        condition.interface_mode = self.interface_mode + other.interface_mode
        condition.tagged_oids    = self.tagged_oids + other.tagged_oids
        condition.untagged_oid   = self.untagged_oid + other.untagged_oid

        return condition


    def __radd__(self, other):
        return self.__add__(other)


    def dump(self):
        items = [
            "remove_from_nb", "is_enabled", "description", "tags",
            "interface_mode", "tagged_oids", "untagged_oid",
        ]

        return {
            **{ k: v for k, v in self.__dict__.items() if k not in [*items] },
            **{ k: self.__dict__[k].dump() for k in items }
        }


class KarteType(Flag):
    WARN   = auto()
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()


class Karte:
    def __init__(self, karte_type, hostname,
                 ifname=None, current=None, desired=None, arguments=[], annotations=[], delete=False):
        self.type          = karte_type
        self.hostname      = hostname
        self.ifname        = ifname
        self.current_state = current
        self.desired_state = desired
        self.arguments     = arguments
        self.annotations   = annotations
        self.delete        = delete


    def dump(self):
        return {
            "Type":        self.type,
            "Device":      self.hostname,
            "Interface":   self.ifname,
            "Arguments":   self.arguments,
            "Current":     self.current_state.dump() if self.current_state is not None else None,
            "Desired":     self.desired_state.dump() if self.desired_state is not None else None,
            "Annotations": [ v.dump() for v in self.annotations ],
            "Delete":      self.delete,
        }


class Annotation:
    def __init__(self, message, severity=1):
        self.message  = message
        self.severity = severity


    def dump(self):
        return {
            "Severity": self.severity,
            "Message": self.message,
        }


    def __str__(self):
        match self.severity:
            case 0:
                severity = "DEBUG"
            case 1:
                severity = "INFO"
            case 2:
                severity = "WARN"
            case 3:
                severity = "CRITICAL"

        return f"{self.message} ({severity})"

