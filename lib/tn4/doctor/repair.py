from tn4.doctor.karte import KarteType


class Repair:
    def __init__(self, ctx, nb_client):
        self.ctx = ctx
        self.cli = nb_client


    def __interface_repair(self, karte):
        if karte.type == KarteType:
            return self.cli.interfaces.update(karte.hostname, karte.ifname, **{
                "description":   karte.desired_state.description,
                "enabled":       karte.desired_state.is_enabled,
                "tags":          karte.desired_state.tags,
                "mode":          karte.desired_state.interface_mode,
                "untagged_vlan": karte.desired_state.untagged_oid,
                "tagged_vlans":  karte.desired_state.tagged_oids,
            })


    def __device_repair(self, karte):
        return


    def by_karte(self, *kartes):
        rt = 0

        for karte in kartes:
            if karte.ifname is None:
                rt += self.__device_repair(karte)
            else:
                rt += self.__interface_repair(karte)

        return rt

