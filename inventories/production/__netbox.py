#!/usr/bin/env python3
# This file is part of Ansible.

def __load_encrypted_secrets():
    with open(VAULT_FILE) as v, open(VAULT_PASSWORD_FILE, "r") as p:
        key = str.encode(p.read().rstrip())
        try:
            vault = VaultLib([(DEFAULT_VAULT_ID_MATCH, VaultSecret(key))])
            raw = vault.decrypt(v.read())
            return yaml.load(raw, Loader=yaml.CLoader)
        except AnsibleVaultError as e:
            print("Failed to decrypt the vault. Check your password and try again:", e, file=sys.stderr)
            sys.exit(1)


def timestamp():
    n = datetime.now()
    return n.strftime("%Y-%m-%d@%H-%M-%S")


def dynamic_inventory():
    ts = timestamp()
    secrets = __load_encrypted_secrets()
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
