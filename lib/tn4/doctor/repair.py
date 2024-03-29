from tn4.doctor.karte import KarteType


class Repair:
    def __init__(self, ctx, nb_client):
        self.ctx = ctx
        self.cli = nb_client


    def __interface_repair(self, karte, debug=False):
        if karte.delete:
            code = self.cli.interfaces.delete(self.ctx, karte.hostname, karte.ifname)
            return code

        _, code = self.cli.interfaces.update(self.ctx, karte.hostname, karte.ifname, **{
            "description":     karte.desired_state.description,
            "enabled":         karte.desired_state.is_enabled,
            "mode":            karte.desired_state.interface_mode,
            "untagged_vlanid": karte.desired_state.untagged_oid,
            "tagged_vlanids":  karte.desired_state.tagged_oids,
            "tags":            karte.desired_state.tags,
            "debug":           debug,
        })

        return code


    def __device_repair(self, karte):
        return


    def by_karte(self, *kartes, debug=False):
        rt = 0

        for karte in kartes:
            if karte.ifname is None:
                rt += self.__device_repair(karte, debug=debug)
            else:
                rt += self.__interface_repair(karte, debug=debug)

        return rt

