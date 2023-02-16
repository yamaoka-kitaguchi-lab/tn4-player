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


class StateBase:
    def __init__(self, nb_object=None):
        self.nb_object = nb_object


    def has(self, flag):
        return flag in self.nb_object


    def has_tag(self, tag):
        return tag in self.nb_object["tags"]


    def is_equal(self, state, attrs=[]):
        if len(attrs) == 0:
            attrs = [ k for k in self.__dict__.keys() if k[:2] != "__" and k[-2:] != "__" ]

        for attr in attrs:
            if getattr(self, attr) != getattr(state, attr):
                return False
        return True


class VlanState(StateBase):
    def __init__(self, nb_object=None):
        super().__init__(nb_object)


class DeviceState(StateBase):
    def __init__(self, nb_object=None):
        super().__init__(nb_object)


class InterfaceState(StateBase):
    def __init__(self, nb_object=None):
        super().__init__(nb_object)
        self.is_enabled     = nb_object["enabled"]
        self.description    = nb_object["description"]
        self.tags           = nb_object["tags"]
        self.interface_mode = nb_object["mode"]["value"]  # None, "access", "tagged", "tagged-all"
        self.tagged_vids    = nb_object["tagged_vids"]
        self.untagged_vid   = nb_object["untagged_vid"]


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


class ReportCategory(Flag):
    WARN   = auto()
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()


class NbckReport:
    def __init__(self, category, current, desired, argument=[], message=None):
        self.category      = category
        self.current_state = current
        self.desired_state = desired
        self.argument      = argument
        self.message       = message
