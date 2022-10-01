import json
import requests


class Context:
    endpoint   = None  # ex) https://netbox.m.noc.titech.ac.jp:8000
    token      = None  # ex) 0123456789abcdef0123456789abcdef01234567
    sites      = None
    devices    = None
    vlans      = None
    addresses  = None
    interfaces = None

    def __init__(self, netbox_url, token):
        self.endpoint = netbox_url.rstrip("/") + "/api"
        self.token = token


class ClientBase:
    def query(self, ctx, location, data=None, update=False):
        code = None
        responses = []
        url = ctx.endpoint + location

        headers = {
            "Authorization": f"Token {ctx.token}",
            "Content-Type":  "application/json",
            "Accept":        "application/json; indent=4"
        }

        if data is None:
            while url:
                raw = requests.get(url, headers=headers, verify=True)

                code = raw.status_code
                if not 200 <= code < 300:
                    return code, []  # early return

                res = json.loads(raw.text)
                responses += res["results"]

                ## If the "next" field has a URL, the results are not yet aligned.
                url = res["next"]

        ## NOTE:
        ## To avoid the overload of NetBox,
        ## large volume editing operations must be split into multiple requests.
        else:
            ptr, size = 0, 100  # size: widnow size of the request division
            while ptr < len(data):
                d = data[ptr:ptr+size]
                raw = None
                if update:
                    raw = requests.patch(url, json.dumps(d), headers=headers, verify=True)
                else:
                    raw = requests.post(url, json.dumps(d), headers=headers, verify=True)

                code = raw.status_code
                if not 200 <= code < 300:
                    return code, []  # early return

                responses += json.loads(raw.text)
                ptr += size

        return code, responses

