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

        self.mgmt_vid_eo = None
        self.mgmt_vid_es = None
        self.mgmt_vid_co = None
        self.mgmt_vid_cs = None

        self.wifi_mgmt_vid_o1 = None
        self.wifi_mgmt_vid_o2 = None
        self.wifi_mgmt_vid_s = None


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
                if Slug.tag_mgmt_vlan_edge_ookayama in vlan["tags"]:
                    self.mgmt_vid_eo = vlan["vid"]
                if Slug.tag_mgmt_vlan_edge_suzukake in vlan["tags"]:
                    self.mgmt_vid_es = vlan["vid"]
                if Slug.tag_mgmt_vlan_core_ookayama in vlan["tags"]:
                    self.mgmt_vid_co = vlan["vid"]
                if Slug.tag_mgmt_vlan_core_suzukake in vlan["tags"]:
                    self.mgmt_vid_cs = vlan["vid"]
                if Slug.tag_wifi_mgmt_vlan_ookayama1 in vlan["tags"]:
                    self.wifi_mgmt_vid_o1 = vlan["vid"]
                if Slug.tag_wifi_mgmt_vlan_ookayama2 in vlan["tags"]:
                    self.wifi_mgmt_vid_o2 = vlan["vid"]
                if Slug.tag_wifi_mgmt_vlan_suzukake in vlan["tags"]:
                    self.wifi_mgmt_vid_s = vlan["vid"]
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
                dev_site = device["site"]["slug"]
                dev_sg = self.all_sites[dev_site]["group"]["slug"]

                if dev_site in self.all_sites:
                    if dev_sg in [Slug.site_group_ookayama_north, Slug.site_group_ookayama_west, Slug.site_group_midorigaoka]:
                        device["wifi_mgmt_vid"] = self.wifi_mgmt_vid_o1
                    elif dev_sg in [Slug.site_group_ookayama_east, Slug.site_group_ookayama_south, Slug.site_group_ishikawadai, Slug.site_group_tamachi]:
                        device["wifi_mgmt_vid"] = self.wifi_mgmt_vid_o2
                    else:
                        device["wifi_mgmt_vid"] = self.wifi_mgmt_vid_s

                self.all_devices[device["name"]] = device
        return self.all_devices


    def get_all_interfaces(self, use_cache=True):
        if not use_cache or not self.all_interfaces:
            all_interfaces = self.query("/dcim/interfaces/")
            for interface in all_interfaces:
                interface["tags"] = [tag["slug"] for tag in interface["tags"]]
                dev_name = interface["device"]["name"]
                int_name = interface["name"]
                if dev_name in self.all_devices:
                    for k in ["device_role", "wifi_mgmt_vid"]:
                        interface[k] = self.all_devices[dev_name][k]
                self.all_interfaces.setdefault(dev_name, {})[int_name] = interface
        return self.all_interfaces
