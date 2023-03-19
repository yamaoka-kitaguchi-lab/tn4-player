from pprint import pprint

from tn4.netbox.slug import Slug
from tn4.doctor.karte import Karte, KarteType


class RepairBase():
    def __init__(self, ctx, karte):
        self.ctx   = ctx
        self.karte = karte


class InterfaceRepair(RepairBase):
    def __init__(self, ctx, karte):
        super().__init__(ctx, karte)


    def repair(self):
        self.ctx.interfaces.update()


class DeviceRepair(RepairBase):
    def __init__(self, ctx, karte):
        super().__init__(ctx, karte)
