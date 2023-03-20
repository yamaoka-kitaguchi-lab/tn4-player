from pprint import pprint

from tn4.netbox.slug import Slug
from tn4.doctor.karte import Karte, KarteType


class RepairBase():
    def __init__(self, ctx):
        self.ctx   = ctx


    def repair_from_karte(self, karte):
        rt = 0
        for assess in karte.all:
            rt += self.repair(assess)

        return rt


class InterfaceRepair(RepairBase):
    def __init__(self, ctx):
        super().__init__(ctx)


    def repair(self, assessment):
        self.ctx.interfaces.update()


class DeviceRepair(RepairBase):
    def __init__(self, ctx):
        super().__init__(ctx)

