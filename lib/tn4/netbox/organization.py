from tn4.netbox.base import ClientBase


class Sites(ClientBase):
    path = '/dcim/sites/'

    def __init__(self):
        super().__init__()

    def fetch_all(self, ctx):
        _, all_sites = self.query(ctx, self.path)
        ctx.sites = all_sites

        return all_sites

