#!/usr/bin/env python3

from argparse import ArgumentParser
from datetime import datetime
import os
import sys
import json

CURDIR              = os.path.dirname(__file__)
LIBRARY_PATH        = os.path.join(CURDIR, "../lib")
VAULT_FILE          = os.path.join(CURDIR, "./group_vars/all/vault.yml")
VAULT_PASSWORD_FILE = os.path.join(CURDIR, "../.secrets/vault-pass.txt")

sys.path.append(LIBRARY_PATH)

from tn4.netbox.base import Context
from tn4.netbox.client import Client
from tn4.helper.utils import load_encrypted_secrets


def timestamp():
    n = datetime.now()
    return n.strftime("%Y-%m-%d@%H-%M-%S")


class NetBox:
    def __init__(self, url=None, token=None):
        secrets = load_encrypted_secrets(VAULT_FILE, VAULT_PASSWORD_FILE)

        if url is None:
            url = secrets["netbox_url"]
        if token is None:
            token = secrets["netbox_api_token"]

        self.ts        = timestamp()
        self.ctx       = Context(endpoint=url, token=token)
        self.cli       = Client()
        self.nbdata    = None
        self.inventory = None


    def fetch_inventory(self, use_cache=False, fetch_all=False):
        if self.nbdata is None:
            self.nbdata = self.cli.fetch_as_inventory(ctx, use_cache=use_cache)

        host_filter = lambda h: self.nbdata[h]["is_ansible_target"] or fetch_all

        self.inventory = {
            **{
                role: {
                    "hosts": {
                        h: {}
                        for h in self.nbdata["_hostnames"]
                        if self.nbdata[h]["role"] == role and host_filter(h)
                    }
                }
                for role in self.nbdata["_roles"]
            },
            "_meta": {
                "hosts": {
                    hostname: {
                        "hostname": hostname,
                        **{
                            key: self.nbdata[hostname][key]
                            for key in [
                                "ansible_host",
                                "apply_groups",       # VRRP-MASTER or VRRP-BACKUP
                                "device_tags",
                                "interfaces",
                                "is_irb",
                                "is_test_device",
                                "lag_members",
                                "manufacturer",
                                "mgmt_vlan",
                                "region",
                                "role",
                                "sitegp",
                                "vlans",
                                "vrrp_group_id",
                                "vrrp_physical_ip4",  # with CIDR length
                                "vrrp_physical_ip6",  # with CIDR length
                                "vrrp_virtual_ip4",   # without CIDR length
                                "vrrp_virtual_ip6",   # without CIDR length
                            ]
                            if key in self.nbdata[hostname]
                        },
                        "datetime": self.ts,
                    }
                    for hostname in self.nbdata["_hostnames"] if host_filter(hostname)
                }
            }
        }

        return self.inventory


if __name__ == "__main__":
    parser = ArgumentParser(description="Ansible - Dynamic Inventory Script")
    parser.add_argument("--use-cache", action="store_true", help="use NetBox cache if $HOME/.cache/tn4-player/*.cache available")
    #parser.add_argument("--debug",     action="store_true", help="debug mode")
    args = parser.parse_args()

    nb = NetBox()
    print(json.dumps(
        nb.fetch_inventory(use_cache=args.use_cache),
        indent=4,
        sort_keys=True,
        ensure_ascii=False
    ))
