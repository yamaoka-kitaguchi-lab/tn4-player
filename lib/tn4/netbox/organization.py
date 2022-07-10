from tn4.netbox.base import ClientBase


class Sites(ClientBase):
    path = '/dcim/sites/'

    def __init__(self):
        super().__init__()

    def get_sites(self, ctx):
        _, all_sites = self.query(ctx, self.path)
        ctx.sites = all_sites

        return all_sites

