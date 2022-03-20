#!/usr/bin/env python3

import json
import os
import requests
import sys
import yaml

from ansible.constants import DEFAULT_VAULT_ID_MATCH
from ansible.parsing.vault import VaultLib
from ansible.parsing.vault import VaultSecret
from ansible.parsing.vault import AnsibleVaultError

VAULT_FILE = os.path.join(os.path.dirname(__file__), "../inventories/production/group_vars/all/vault.yml")
VAULT_PASSWORD_FILE = os.path.join(os.path.dirname(__file__), "../.secrets/vault-pass.txt")


def load_encrypted_secrets():
    with open(VAULT_FILE) as v, open(VAULT_PASSWORD_FILE, "r") as p:
        key = str.encode(p.read().rstrip())
        try:
            vault = VaultLib([(DEFAULT_VAULT_ID_MATCH, VaultSecret(key))])
            raw = vault.decrypt(v.read())
            return yaml.load(raw, Loader=yaml.CLoader)
        except AnsibleVaultError as e:
            print("Failed to decrypt the vault. Check your password and try again:", e, file=sys.stderr)
            sys.exit(1)


class NetBoxClient:
    def __init__(self, netbox_url, netbox_api_token):
        self.netbox_url = netbox_url
        self.api_endpoint = netbox_url.rstrip("/") + "/api"
        self.token = netbox_api_token
        self.all_sites = {}
        self.all_vlans = {}
        self.all_devices = {}
        self.all_interfaces = {}
        self.all_addresses = []


    def query(self, request_path):
        responses = []
        url = self.api_endpoint + request_path
        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type":  "application/json",
            "Accept":                "application/json; indent=4"
        }

        while url:
            raw = requests.get(url, headers=headers, verify=True)
            res = json.loads(raw.text)
            responses += res["results"]
            url = res["next"]
        return responses


    def get_all_sites(self, use_cache=True):
        if not use_cache or not self.all_sites:
            all_sites = self.query("/dcim/sites/")
            for site in all_sites:
                self.all_sites[site["slug"]] = site
        return self.all_sites


    def get_all_vlans(self, use_cache=True):
        if not use_cache or not self.all_vlans:
            all_vlans = self.query("/ipam/vlans/")
            for vlan in all_vlans:
                vlan["tags"] = [tag["slug"] for tag in vlan["tags"]]
                self.all_vlans[vlan["id"]] = vlan
        return self.all_vlans


    def get_all_addresses(self, use_cache=True):
        if not use_cache or not self.all_addresses:
            self.all_addresses = self.query("/ipam/ip-addresses/")
            for address in self.all_addresses:
                address["tags"] = [tag["slug"] for tag in address["tags"]]
        return self.all_addresses


    def get_all_devices(self, use_cache=True):
        if not use_cache or not self.all_devices:
            all_devices = self.query("/dcim/devices/")
            for device in all_devices:
                device["tags"] = [tag["slug"] for tag in device["tags"]]
                if device["site"]["slug"] in self.all_sites:
                    device["region"] = self.all_sites[device["site"]["slug"]]
                self.all_devices[device["name"]] = device
        return self.all_devices


    def get_all_interfaces(self, use_cache=True):
        if not use_cache or not self.all_interfaces:
            all_interfaces = self.query("/dcim/interfaces/")
            for interface in all_interfaces:
                interface["tags"] = [tag["slug"] for tag in interface["tags"]]
                if interface["device"]["name"] in self.all_devices:
                    interface["site"] = self.all_devices[interface["device"]["name"]]["site"]
                    interface["region"] = self.all_devices[interface["device"]["name"]]["region"]
                dev_name = interface["device"]["name"]
                int_name = interface["name"]
                self.all_interfaces.setdefault(dev_name, {})[int_name] = interface
        return self.all_interfaces
