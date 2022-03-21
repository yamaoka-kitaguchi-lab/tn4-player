#!/usr/bin/env python3

import json
import os
import re
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


class Slug:
    role_core_sw = "core_sw"
    role_edge_sw = "edge_sw"

    site_group_ookayama_north = "ookayama-n"
    site_group_ookayama_south = "ookayama-s"
    site_group_ookayama_east  = "ookayama-e"
    site_group_ookayama_west  = "ookayama-w"
    site_group_ishikawadai    = "ishikawadai"
    site_group_midorigaoka    = "midorigaoka"
    site_group_tamachi        = "tamachi"

    tag_core_downstream           = "downlink"
    tag_edge_upstream             = "uplink"
    tag_mgmt_vlan_border_ookayama = "mgmt-vlan-bo"
    tag_mgmt_vlan_border_suzukake = "mgmt-vlan-bs"
    tag_mgmt_vlan_core_ookayama   = "mgmt-vlan-co"
    tag_mgmt_vlan_core_suzukake   = "mgmt-vlan-cs"
    tag_mgmt_vlan_edge_ookayama   = "mgmt-vlan-eo"
    tag_mgmt_vlan_edge_suzukake   = "mgmt-vlan-es"
    tag_vlan_ookayama             = "vlan-o"
    tag_vlan_suzukake             = "vlan-s"
    tag_wifi_mgmt_vlan_ookayama1  = "wlan-mgmt-vlan-o1"
    tag_wifi_mgmt_vlan_ookayama2  = "wlan-mgmt-vlan-o2"
    tag_wifi_mgmt_vlan_suzukake   = "wlan-mgmt-vlan-s"
    tag_wifi                      = "wifi"
    tag_wifi_sw                   = "poe-sw"


class NetBoxClient:
    def __init__(self, netbox_url, netbox_api_token):
        self.netbox_url = netbox_url
        self.api_endpoint = netbox_url.rstrip("/") + "/api"
        self.token = netbox_api_token
        self.all_sites = {}       # key: site slug, value site object
        self.all_vlans = {}       # key: vlan object id not vid, value: vlan object
        self.all_devices = {}     # key: device name, value: device object
        self.all_interfaces = {}  # key: device name, subkey: interface name, value: interface object
        self.all_addresses = []

        self.mgmt_vlanid_eo = None
        self.mgmt_vlanid_es = None
        self.mgmt_vlanid_co = None
        self.mgmt_vlanid_cs = None

        self.wifi_vlanids_o = []
        self.wifi_vlanids_s = []
        self.wifi_mgmt_vlanid_o1 = None
        self.wifi_mgmt_vlanid_o2 = None
        self.wifi_mgmt_vlanid_s = None


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
                    self.mgmt_vlanid_eo = vlan["id"]
                if Slug.tag_mgmt_vlan_edge_suzukake in vlan["tags"]:
                    self.mgmt_vlanid_es = vlan["id"]
                if Slug.tag_mgmt_vlan_core_ookayama in vlan["tags"]:
                    self.mgmt_vlanid_co = vlan["id"]
                if Slug.tag_mgmt_vlan_core_suzukake in vlan["tags"]:
                    self.mgmt_vlanid_cs = vlan["id"]

                if Slug.tag_wifi_mgmt_vlan_ookayama1 in vlan["tags"]:
                    self.wifi_mgmt_vlanid_o1 = vlan["id"]
                if Slug.tag_wifi_mgmt_vlan_ookayama2 in vlan["tags"]:
                    self.wifi_mgmt_vlanid_o2 = vlan["id"]
                if Slug.tag_wifi_mgmt_vlan_suzukake in vlan["tags"]:
                    self.wifi_mgmt_vlanid_s = vlan["id"]
                if Slug.tag_wifi in vlan["tags"] and vlan["status"]["value"] == "active":
                    if Slug.tag_vlan_ookayama in vlan["tags"]:
                        self.wifi_vlanids_o.append(vlan["id"])
                    if Slug.tag_vlan_suzukake in vlan["tags"]:
                        self.wifi_vlanids_s.append(vlan["id"])

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
                        device["wifi_mgmt_vlanid"] = self.wifi_mgmt_vlanid_o1
                        device["wifi_vlanids"] = self.wifi_vlanids_o
                    elif dev_sg in [Slug.site_group_ookayama_east, Slug.site_group_ookayama_south, Slug.site_group_ishikawadai, Slug.site_group_tamachi]:
                        device["wifi_mgmt_vlanid"] = self.wifi_mgmt_vlanid_o2
                        device["wifi_vlanids"] = self.wifi_vlanids_o
                    else:
                        device["wifi_mgmt_vlanid"] = self.wifi_mgmt_vlanid_s
                        device["wifi_vlanids"] = self.wifi_vlanids_s

                device["hostname"] = device["name"]
                device["is_vc_member"] = False
                device["vc_chassis_number"] = 0
                if device["device_role"]["slug"] == Slug.role_edge_sw:
                    hostname_reg = re.match("([\w|-]+) \((\d+)\)", device["name"])
                    if hostname_reg is not None:
                        device["hostname"] = hostname_reg.group(1)
                        device["is_vc_member"] = True
                        device["vc_chassis_number"] = hostname_reg.group(2)

                self.all_devices[device["name"]] = device
        return self.all_devices


    def get_all_interfaces(self, use_cache=True):
        allowed_int_types_virtual = ["lag"]  # Ignore virtual type interfaces
        allowed_int_types_ethernet_utp = [
             "1000base-t", "2.5gbase-t", "5gbase-t", "10gbase-t",
        ]
        allowed_int_types_ethernet = [
            *allowed_int_types_ethernet_utp,
            "100base-tx", "1000base-x-gbic", "1000base-x-sfp", "10gbase-cx4", "10gbase-x-sfpp", "10gbase-x-xfp",
            "10gbase-x-xenpak", "10gbase-x-x2", "25gbase-x-sfp28", "40gbase-x-qsfpp", "50gbase-x-sfp28", "100gbase-x-cfp",
            "100gbase-x-cfp2", "100gbase-x-cfp4", "100gbase-x-cpak", "100gbase-x-qsfp28", "200gbase-x-cfp2",
            "200gbase-x-qsfp56", "400gbase-x-qsfpdd", "400gbase-x-osfp",
        ]
        allowed_int_types = [*allowed_int_types_virtual, *allowed_int_types_ethernet]

        if not use_cache or not self.all_interfaces:
            all_interfaces = self.query("/dcim/interfaces/")
            for interface in all_interfaces:
                interface["tags"] = [tag["slug"] for tag in interface["tags"]]

                dev_name = interface["device"]["name"]
                int_name = interface["name"]
                if dev_name in self.all_devices:
                    for k in ["device_role", "wifi_mgmt_vlanid", "wifi_vlanids", "hostname", "is_vc_member", "vc_chassis_number"]:
                        interface[k] = self.all_devices[dev_name][k]

                interface["is_deploy_target"] = interface["type"]["value"] in allowed_int_types
                interface["is_lag_parent"] = interface["type"]["value"] == "lag"
                interface["is_lag_member"] = interface["lag"] is not None
                interface["is_utp"] = interface["type"]["value"] in allowed_int_types_ethernet_utp
                interface["is_to_core"] = interface["device_role"]["slug"] == Slug.role_edge_sw and Slug.tag_edge_upstream in interface["tags"]
                interface["is_to_edge"] = interface["device_role"]["slug"] == Slug.role_core_sw and Slug.tag_core_downstream in interface["tags"]
                interface["is_to_ap"] = interface["device_role"]["slug"] == Slug.role_edge_sw and Slug.tag_wifi in interface["tags"]
                interface["is_to_poesw"] = interface["device_role"]["slug"] == Slug.role_edge_sw and Slug.tag_wifi_sw in interface["tags"]

                all_vlan_ids = []
                all_vids = []
                interface["tagged_vlanids"] = None
                interface["tagged_vids"] = None
                interface["untagged_vlanid"] = None
                interface["untagged_vid"] = None

                if interface["tagged_vlans"] is not None:
                    interface["tagged_vlanids"] = [v["id"] for v in interface["tagged_vlans"]]
                    interface["tagged_vids"] = [v["vid"] for v in interface["tagged_vlans"]]
                    all_vlan_ids.extend(interface["tagged_vlanids"])
                    all_vids.extend(interface["tagged_vids"])
                if interface["untagged_vlan"] is not None:
                    interface["untagged_vlanid"] = interface["untagged_vlan"]["id"]
                    interface["untagged_vid"] = interface["untagged_vlan"]["vid"]
                    all_vlan_ids.append(interface["untagged_vlanid"])
                    all_vids.append(interface["untagged_vid"])

                interface["all_vlanids"] = list(set(all_vlan_ids))
                interface["all_vids"] = list(set(all_vids))

                self.all_interfaces.setdefault(dev_name, {})[int_name] = interface
        return self.all_interfaces