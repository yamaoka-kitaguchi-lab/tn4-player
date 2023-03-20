from pprint import pprint

from tn4.netbox.slug import Slug
from tn4.doctor.karte import Karte, KarteType


class Repair():
    def __init__(self, ctx):
        self.ctx   = ctx


    def __interface_repair(self, karte):
        self.ctx.interfaces.update()


    def __device_repair(self, karte):
        pass


    def repair(self, karte):
        if karte.ifname is None:
            return self.__device_repair(karte)
        else:
            return self.__interface_repair(karte)

