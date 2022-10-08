#!/usr/bin/env python3

from argparse import ArgumentParser
from datetime import datetime
import os
import sys
import json

CURDIR              = os.path.dirname(__file__)
LIBRARY_PATH        = os.path.join(CURDIR, "../../lib")
VAULT_FILE          = os.path.join(CURDIR, "./group_vars/all/vault.yml")
VAULT_PASSWORD_FILE = os.path.join(CURDIR, "../../.secrets/vault-pass.txt")

sys.path.append(LIBRARY_PATH)

from tn4.netbox.base import Context
from tn4.netbox.client import Client
from tn4.helper.utils import load_encrypted_secrets


def timestamp():
    n = datetime.now()
    return n.strftime("%Y-%m-%d@%H-%M-%S")


class NetBox:
    def __init__(self):
        self.ts        = timestamp()
        secrets   = load_encrypted_secrets(VAULT_FILE, VAULT_PASSWORD_FILE)
        self.ctx       = Context(endpoint=secrets["netbox_url"], token=secrets["netbox_api_token"])
        self.cli       = Client()
        self.nbdata    = None
        self.inventory = None


    def fetch_inventory(self, use_cache=False):
        if self.nbdata is None:
            self.nbdata = cli.fetch_as_inventory(ctx, use_cache=use_cache)

        self.inventory = {
            **{
                role: {
                    "hosts": [ h for h in self.nbdata["_hostnames"] if self.nbdata[h]["role"] == role ]
                }
                for role in self.nbdata["_roles"]
            },
            "_meta": {
                "hostvars": {
                    hostname: {
                        "hostname": hostname,
                        **{
                            key: self.nbdata[hostname][key]
                            for key in [
                                "ansible_host",
                                "device_tags",
                                "interfaces",
                                "is_test_device",
                                "lag_members",
                                "manufacturer",
                                "mgmt_vlan",
                                "region",
                                "role",
                                "sitegp",
                                "vlans",
                            ]
                        },
                        "datetime": self.ts,
                    }
                    for hostname in self.nbdata["_hostnames"]
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
