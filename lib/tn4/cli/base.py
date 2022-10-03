from pprint import pprint
import jinja2
import os
import sys
import time

CURDIR             = os.path.dirname(__file__)
ANSIBLE_PRODUCTION = os.path.join(CURDIR, "../../../inventories/production")
sys.path.append(ANSIBLE_PRODUCTION)

from netbox import dynamic_inventory


class CommandBase:
    def fetch_inventory(self, **kwargs):
        inventory = dynamic_inventory()

