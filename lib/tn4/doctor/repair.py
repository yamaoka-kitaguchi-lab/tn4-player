from pprint import pprint

from tn4.netbox.slug import Slug
from tn4.doctor.karte import Karte, KarteType


class Repair:
    def __init__(self, ctx):
        self.ctx   = ctx


    def __interface_repair(self, karte):
        self.ctx.interfaces.update()


    def __device_repair(self, karte):
        pass


    def by_karte(self, *kartes):
        rt = 0

        for karte in kartes:
            if karte.ifname is None:
                rt += self.__device_repair(karte)
            else:
                rt += self.__interface_repair(karte)

        return rt

