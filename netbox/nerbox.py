
class NetBoxClient:
  def __init__(self, netbox_url, netbox_api_token):
    self.api_endpoint = netbox_url.rstrip("/") + "/api"
    self.token = netbox_api_token
    self.all_sites = []
    self.all_vlans = []
    self.all_devices = []
    self.all_interfaces = []
    self.all_addresses = []


  def query(self, request_path):
    responses = []
    url = self.api_endpoint + request_path
    headers = {
      "Authorization": f"Token {self.token}",
      "Content-Type":  "application/json",
      "Accept":        "application/json; indent=4"
    }

    while url:
      raw = requests.get(url, headers=headers, verify=True)
      res = json.loads(raw.text)
      responses += res["results"]
      url = res["next"]
    return responses


  def get_all_sites(self, use_cache=True):
    if not use_cache or not self.all_sites:
      self.all_sites = self.query("/dcim/sites/")
    return self.all_sites


  def get_all_vlans(self, use_cache=True):
    if not use_cache or not self.all_vlans:
      self.all_vlans = self.query("/ipam/vlans/")
      for vlan in self.all_vlans:
        vlan["tags"] = [tag["slug"] for tag in vlan["tags"]]
    return self.all_vlans


  def get_all_devices(self, use_cache=True):
    if not use_cache or not self.all_devices:
      self.all_devices = self.query("/dcim/devices/")
      for device in self.all_devices:
        device["tags"] = [tag["slug"] for tag in device["tags"]]
    return self.all_devices


  def get_all_interfaces(self, use_cache=True):
    if not use_cache or not self.all_interfaces:
      self.all_interfaces = self.query("/dcim/interfaces/")
      for interface in self.all_interfaces:
        interface["tags"] = [tag["slug"] for tag in interface["tags"]]
    return self.all_interfaces


  def get_all_addresses(self, use_cache=True):
    if not use_cache or not self.all_addresses:
      self.all_addresses = self.query("/ipam/ip-addresses/")
      for address in self.all_addresses:
        address["tags"] = [tag["slug"] for tag in address["tags"]]
    return self.all_addresses








from ansible.constants import DEFAULT_VAULT_ID_MATCH
from ansible.parsing.vault import VaultLib
from ansible.parsing.vault import VaultSecret
from ansible.parsing.vault import AnsibleVaultError

VAULT_FILE = os.path.join(os.path.dirname(__file__), "./group_vars/all/vault.yml")
VAULT_PASSWORD_FILE = os.path.join(os.path.dirname(__file__), "../../.secrets/vault-pass.txt")




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
