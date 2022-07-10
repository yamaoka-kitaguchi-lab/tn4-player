

    def get_all_addresses(self, use_cache=True):
        if not use_cache or not self.all_addresses:
            self.all_addresses = self.query("/ipam/ip-addresses/")
            for address in self.all_addresses:
                address["tags"] = [tag["slug"] for tag in address["tags"]]
        return self.all_addresses
