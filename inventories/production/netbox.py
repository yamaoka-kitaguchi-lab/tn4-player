#!/usr/bin/env python3

import os
import sys
sys.path.append('lib')

from tn4.netbox.base import Context
from tn4.netbox.client import Client
from tn4.utils import load_encrypted_secrets


VAULT_FILE = os.path.join(os.path.dirname(__file__), "./group_vars/all/vault.yml")
VAULT_PASSWORD_FILE = os.path.join(os.path.dirname(__file__), "../../.secrets/vault-pass.txt")


def timestamp():
    n = datetime.now()
    return n.strftime("%Y-%m-%d@%H-%M-%S")


def dynamic_inventory():
    ts = timestamp()
    secrets = load_encrypted_secrets(VAULT_FILE, VAULT_PASSWORD_FILE)
    nb = NetBoxClient(secrets["netbox_url"], secrets["netbox_api_token"])
    cf = DevConfig(nb)

    devices = cf.get_all_devices()
    inventory = {
        "_meta": {
            "hostvars": {}
        }
    }

    for device in devices:
        hostname = device["hostname"]
        role = device["role"]

        try:
            inventory[role]["hosts"].append(hostname)
        except KeyError:
            inventory[role] = {"hosts": [hostname]}

        interfaces = cf.get_device_interfaces(role, hostname)
        inventory["_meta"]["hostvars"][hostname] = {
            "hostname":       hostname,
            "region":         device["region"],
            "manufacturer":   cf.get_manufacturer(hostname),
            "vlans":          cf.get_device_vlans(hostname),
            "mgmt_vlan":      cf.get_mgmt_vlan(role, device["region"]),
            "interfaces":     interfaces,
            "lag_members":    cf.get_lag_members(hostname, interfaces),
            "is_test_device": DevConfig.TAG_TEST in device["tags"],
            "ansible_host":   cf.get_ip_address(hostname),
            "datetime":       ts,
        }

    return inventory


if __name__ == "__main__":
    inventory = dynamic_inventory()
    print(json.dumps(inventory))

