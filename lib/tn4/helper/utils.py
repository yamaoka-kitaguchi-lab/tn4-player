from ansible.constants import DEFAULT_VAULT_ID_MATCH
from ansible.parsing.vault import AnsibleVaultError, VaultLib, VaultSecret
import yaml


def load_encrypted_secrets(vault_file, vault_password_file):
    with open(vault_file) as v, open(vault_password_file, "r") as p:
        key = str.encode(p.read().rstrip())

        try:
            vault = VaultLib([(DEFAULT_VAULT_ID_MATCH, VaultSecret(key))])
            raw = vault.decrypt(v.read())
            return yaml.load(raw, Loader=yaml.CLoader)

        except AnsibleVaultError as e:
            raise Exception(f"Failed to decrypt the vault. Check your password and try again. {e}")

