from enum import Flag, auto


class Annotation:
    def __init__(self, message, severity=1):
        self.message = message


class InterfaceCondition:
    def __init__(self, argument, priority=100, manual_repair=False):
        self.argument            = argument
        self.priority            = priority
        self.manual_repair       = manual_repair  # if true, nbck skips repairing but just present messages
        self.remove_from_nb      = ConditionalValue()

        self.is_enabled          = ConditionalValue()
        self.description         = ConditionalValue()
        self.tags                = ConditionalValue()
        self.is_tagged_vlan_mode = ConditionalValue()
        self.tagged_vids         = ConditionalValue()
        self.untagged_vid        = ConditionalValue()


class Category(Flag):
    WARN   = auto()
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()


class Assessment:
    def __init__(self, category, current=None, desired=None, arguments=[], annotations=[]):
        self.category      = category
        self.current_state = current
        self.desired_state = desired
        self.arguments     = arguments
        self.annotations   = annotations

