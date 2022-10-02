#!/usr/bin/env python3

import os
import sys

CURDIR              = os.path.dirname(__file__)
LIBRARY_PATH        = os.path.join(CURDIR, "../../lib")
VAULT_FILE          = os.path.join(CURDIR, "./group_vars/all/vault.yml")
VAULT_PASSWORD_FILE = os.path.join(CURDIR, "../../.secrets/vault-pass.txt")

sys.path.append(LIBRARY_PATH)

from tn4.netbox.base import Context
from tn4.netbox.client import Client
from tn4.utils import load_encrypted_secrets


def timestamp():
    n = datetime.now()
    return n.strftime("%Y-%m-%d@%H-%M-%S")


def dynamic_inventory(use_cache=False):
    ts = timestamp()
    secrets = load_encrypted_secrets(VAULT_FILE, VAULT_PASSWORD_FILE)
    ctx = Context(endpoint=secrets["netbox_url"], token=secrets["netbox_api_token"])
    cli = Client()
    nbdata = cli.fetch_all(ctx, use_cache=use_cache)

    inventory = {
        **{
            role: {
                "hosts": [ h for h in nbdata["_hostnames"] if nbdata[h]["role"] == role ]
            }
            for role in nbdata["_roles"]
        },
        "_meta": {
            "hostvars": {
                hostname: {
                    "hostname":       hostname,
                    "region":         nbdata[hostname]["region"],
                    "manufacturer":   nbdata[hostname]["manufacturer"],
                    "interfaces":     nbdata[hostname]["interfaces"],
                    "lag_members":    nbdata[hostname]["lag_members"],
                    "vlans":          nbdata[hostname]["vlans"],
                    "mgmt_vlan":      nbdata[hostname]["mgmt_vlan"],
                    "is_test_device": nbdata[hostname]["is_test_device"],
                    "ansible_host":   nbdata[hostname]["mgmt_ip_address"],
                    "datetime":       ts,
                }
                for hostname in nbdata["_hostnames"]
            }
        }
    }

    return inventory


if __name__ == "__main__":
    inventory = dynamic_inventory()
    print(json.dumps(inventory, indent=4, sort_keys=True, ensure_ascii=False))
