from enum import Flag, auto


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
        self.is_enabled  = nb_object["enabled"]
        self.description = nb_object["description"]
        self.tags        = nb_object["tags"]

        try:
            self.is_tagged_vlan_mode = nb_object["mode"]["value"] == "tagged"
        except KeyError:
            self.is_tagged_vlan_mode = False

        self.tagged_vids  = set(nb_object["tagged_vids"])
        self.untagged_vid = nb_object["untagged_vid"]


    def merge(self, state):
        self.tags.append(state.tags)
        if state.tagged_vids is not None:
            self.is_tagged_vlan_mode = True
            self.tagged_vids.add(state.tagged_vids)
        if state.untagged_vid is not None:
            self.untagged_vid = state.untagged_vid


class Category(Flag):
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


    def merge(self, new_report):
        self.desired_state.merge(new_report.desired_state)
        self.argument.append(new_report.argument)
        self.message.append(new_report.message)

