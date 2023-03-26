# tn4-player
[![CodeQL](https://github.com/yamaoka-kitaguchi-lab/tn4-player/actions/workflows/github-code-scanning/codeql/badge.svg?branch=main)](https://github.com/yamaoka-kitaguchi-lab/tn4-player/actions/workflows/github-code-scanning/codeql) [![GitHub last commit](https://img.shields.io/github/last-commit/yamaoka-kitaguchi-lab/tn4-player)](https://github.com/yamaoka-kitaguchi-lab/tn4-player/commit/HEAD) [![GitHub commit activity](https://img.shields.io/github/commit-activity/y/yamaoka-kitaguchi-lab/tn4-player)](https://github.com/yamaoka-kitaguchi-lab/tn4-player/commits/master)

Titanet4 as Code - inventory management with NetBox and automated deployment with Ansible.

## Getting started with tn4 command

### Supported commands of tn4-player

```
% tn4

These are common tn4 examples:

    Render Jinaj2 templates and export them as *.cfg files

        tn4 config --use-cache /tmp/out
        tn4 config --areas ookayama-s,ishikawadai --no-hosts minami3 /tmp/out
        tn4 config --template /tmp/custom.j2 /tmp/out

    Fetch running configs and save them as *.cfg files

        tn4 config --remote-fetch /tmp/out

    Provisioning Titanet4 with Ansible

        tn4 deploy
        tn4 deploy -vv
        tn4 deploy --dryrun
        tn4 deploy --tags test --no-vendors cisco --commit-confirm 1
        tn4 deploy --tags test --no-vendors cisco --early-exit
        tn4 deploy --vendors juniper --no-roles core_sw --overwrite /tmp/junos.j2

    Scan NetBox and repair inconsistencies (ex-nbck command)

        tn4 doctor --use-cache --diagnose-only
        tn4 doctor --force-repair --tags test --areas ookayama

    Manage branch VLANs and VRRP group

        tn4 doctor branch-vlan --add v999_noc.life.o --prefix 131.112.126.0/26 --vrrp-master 131.112.126.47 --vrrp-backup 131.112.126.46 --vrrp-vip 131.112.126.42
        tn4 doctor branch-vlan --delete v999_noc.life.o

`tn4 --help` list all optional command line arguments
```

```
% tn4 --help

usage: tn4 [-h] [--version] [--debug] {config,c,deploy,d,doctor,x} ...

Run without arguments to see common usage

options:
  -h, --help            show this help message and exit
  --version             show software version and exit
  --debug               enable tn4-cli debug mode. only for developers and should NOT be set if you don't know
                        what to expect

commands:
  COMMAND [ARGS]

  {config,c,deploy,d,doctor,x}
    config (c)          render Jinja2 templates or fetch running configs using Ansible
    deploy (d)          provisioning Titanet4 with Ansible
    doctor (x)          scan and repair NetBox inconsistency
```

### tn4 config

```
% tn4 config --help

usage: tn4 config [-h] [--netbox-url NETBOX_URL] [--netbox-token NETBOX_TOKEN] [--use-cache] [--hosts HOSTS]
                  [--no-hosts NO_HOSTS] [--areas AREAS] [--no-areas NO_AREAS] [--roles ROLES]
                  [--no-roles NO_ROLES] [--vendors VENDORS] [--no-vendors NO_VENDORS] [--tags TAGS]
                  [--no-tags NO_TAGS] [--remote-fetch] [--template CUSTOM_J2_PATH] [--as-ansible-inventory]
                  private_dir

tn4 config - Rendering Jinja2 templates and exporting them as *.cfg files

positional arguments:
  private_dir           base directory for data exporting

options:
  -h, --help            show this help message and exit
  --netbox-url NETBOX_URL
                        custom NetBox URL (e.g. http://netbox00.m.noc.titech.ac.jp)
  --netbox-token NETBOX_TOKEN
                        custom NetBox API token
  --use-cache           skip NetBox fetching and use local cache if available (~/.cache/tn4-player/*.cache)
  --hosts HOSTS         comma-separated list of target hostnames
  --no-hosts NO_HOSTS   inverted option of ```--hosts```
  --areas AREAS         comma-separated list of target regions or site groups (e.g. ookayama-n,suzukake)
  --no-areas NO_AREAS   inverted option of ```--areas```
  --roles ROLES         comma-separated list of target device roles (e.g. edge_sw)
  --no-roles NO_ROLES   inverted option of ```--roles```
  --vendors VENDORS     comma-separated list of target manufacturers (e.g. juniper)
  --no-vendors NO_VENDORS
                        inverted option of ```--vendors```
  --tags TAGS           comma-separated list of target tags (e.g. test)
  --no-tags NO_TAGS     inverted option of ```--tags```
  --remote-fetch        fetch and save running configs using Ansible and exit
  --template CUSTOM_J2_PATH
                        use custom Jinja2 template instead of the defautls
  --as-ansible-inventory
                        export the raw inventory json instead of rendered configs
```

### tn4 deploy

```
% tn4 deploy --help

usage: tn4 deploy [-h] [--netbox-url NETBOX_URL] [--netbox-token NETBOX_TOKEN] [--use-cache] [--hosts HOSTS]
                  [--no-hosts NO_HOSTS] [--areas AREAS] [--no-areas NO_AREAS] [--roles ROLES]
                  [--no-roles NO_ROLES] [--vendors VENDORS] [--no-vendors NO_VENDORS] [--tags TAGS]
                  [--no-tags NO_TAGS] [--overwrite OVERWRITE_J2_PATH] [--commit-confirm COMMIT_CONFIRM_MIN]
                  [--dryrun] [--early-exit] [-v]

tn4 deploy - Provisioning Titanet4 with Ansible using NetBox as inventory

options:
  -h, --help            show this help message and exit
  --netbox-url NETBOX_URL
                        custom NetBox URL (e.g. http://netbox00.m.noc.titech.ac.jp)
  --netbox-token NETBOX_TOKEN
                        custom NetBox API token
  --use-cache           skip NetBox fetching and use local cache if available (~/.cache/tn4-player/*.cache)
  --hosts HOSTS         comma-separated list of target hostnames
  --no-hosts NO_HOSTS   inverted option of ```--hosts```
  --areas AREAS         comma-separated list of target regions or site groups (e.g. ookayama-n,suzukake)
  --no-areas NO_AREAS   inverted option of ```--areas```
  --roles ROLES         comma-separated list of target device roles (e.g. edge_sw)
  --no-roles NO_ROLES   inverted option of ```--roles```
  --vendors VENDORS     comma-separated list of target manufacturers (e.g. juniper)
  --no-vendors NO_VENDORS
                        inverted option of ```--vendors```
  --tags TAGS           comma-separated list of target tags (e.g. test)
  --no-tags NO_TAGS     inverted option of ```--tags```
  --overwrite OVERWRITE_J2_PATH
                        use custom Jinja2 template instead of the defautls to overwrite configs
  --commit-confirm COMMIT_CONFIRM_MIN
                        set the time (minutes) to use in ```commit confirm```. only effective on juniper hosts
  --dryrun              simulate a command's result without actually running it
  --early-exit          just show the list of deploy targets and exit. most preferred
  -v                    increase the verbosity with multiple v's (up to 5)
```

### tn4 doctor

```
% tn4 doctor --help

usage: tn4 doctor [-h] [--netbox-url NETBOX_URL] [--netbox-token NETBOX_TOKEN] [--use-cache] [--hosts HOSTS]
                  [--no-hosts NO_HOSTS] [--areas AREAS] [--no-areas NO_AREAS] [--roles ROLES]
                  [--no-roles NO_ROLES] [--vendors VENDORS] [--no-vendors NO_VENDORS] [--tags TAGS]
                  [--no-tags NO_TAGS] [--diagnose-only] [--force-repair]
                  {branch-vlan} ...

tn4 doctor - Scanning NetBox and repairing inconsistencies, also providing CLI-based CRUD operations

options:
  -h, --help            show this help message and exit
  --netbox-url NETBOX_URL
                        custom NetBox URL (e.g. http://netbox00.m.noc.titech.ac.jp)
  --netbox-token NETBOX_TOKEN
                        custom NetBox API token
  --use-cache           skip NetBox fetching and use local cache if available (~/.cache/tn4-player/*.cache)
  --hosts HOSTS         comma-separated list of target hostnames
  --no-hosts NO_HOSTS   inverted option of ```--hosts```
  --areas AREAS         comma-separated list of target regions or site groups (e.g. ookayama-n,suzukake)
  --no-areas NO_AREAS   inverted option of ```--areas```
  --roles ROLES         comma-separated list of target device roles (e.g. edge_sw)
  --no-roles NO_ROLES   inverted option of ```--roles```
  --vendors VENDORS     comma-separated list of target manufacturers (e.g. juniper)
  --no-vendors NO_VENDORS
                        inverted option of ```--vendors```
  --tags TAGS           comma-separated list of target tags (e.g. test)
  --no-tags NO_TAGS     inverted option of ```--tags```
  --diagnose-only       scan NetBox, present diagnosis report, and exit
  --force-repair        skip confirmation and perform NetBox repair immediately if needed

commands:
  COMMAND [ARGS]

  {branch-vlan}
    branch-vlan         branch network management utilities
```

### tn4 doctor branch-vlan

```
% tn4 doctor branch-vlan --help

usage: tn4 doctor branch-vlan [-h] [--add] [--prefix CIDR_PREFIX] [--prefix-v6 CIDR_PREFIX6]
                              [--vrrp-master VRRP_MASTER_IP] [--vrrp-backup VRRP_BACKUP_IP]
                              [--vrrp-vip VRRP_VIP] [--vrrp-master-v6 VRRP_MASTER_IP6]
                              [--vrrp-backup-v6 VRRP_BACKUP_IP6] [--vrrp-vip-v6 VRRP_VIP6] [--delete]
                              vlan_name

tn4 doctor branch-vlan - add or remove branch VLAN and setup VRRP

positional arguments:
  vlan_name             branch VLAN name

options:
  -h, --help            show this help message and exit
  --add                 add branch VLAN and setup VRRP
  --prefix CIDR_PREFIX  CIDR format of branch VLAN prefix (IPv4)
  --prefix-v6 CIDR_PREFIX6
                        CIDR format of branch VLAN prefix (IPv6)
  --vrrp-master VRRP_MASTER_IP
                        VRRP master IP address without CIDR length. must be inside the VLAN prefix (IPv4)
  --vrrp-backup VRRP_BACKUP_IP
                        VRRP backup IP address without CIDR length. must be inside the VLAN prefix (IPv4)
  --vrrp-vip VRRP_VIP   VRRP VIP address without CIDR length. must be inside the VLAN prefix (IPv4)
  --vrrp-master-v6 VRRP_MASTER_IP6
                        VRRP master IP address without CIDR length. must be inside the VLAN prefix (IPv6)
  --vrrp-backup-v6 VRRP_BACKUP_IP6
                        VRRP backup IP address without CIDR length. must be inside the VLAN prefix (IPv6)
  --vrrp-vip-v6 VRRP_VIP6
                        VRRP VIP address without CIDR length. must be inside the VLAN prefix (IPv6)
  --delete              delete branch VLAN and clear VRRP

```


## Hints
Some hints and tips from the author.

### Build the EE container with ansible-builder
See [https://quay.io/repository/ansible/ansible-runner](https://quay.io/repository/ansible/ansible-runner?tab=tags) to check the latest tag and edit Pipfile if needed. Ansible Builder will take about 20 minutes.

```
% mv docker.ee/Dockerfile docker.ee/Dockerfile.base
% pipenv update
% pipenv requirements > docker.ee/requirements.txt
% docker build -t ghcr.io/yamaoka-kitaguchi-lab/tn4-player/ansible-runner-base:latest - < docker.ee/Dockerfile.base
% pipenv run ansible-builder
```

## License
This is free and unencumbered public domain software. For more information, see [http://unlicense.org/](http://unlicense.org/) or the accompanying [LICENSE](LICENSE) file.

