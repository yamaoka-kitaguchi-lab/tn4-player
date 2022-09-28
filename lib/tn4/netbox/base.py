import json
import requests


class Context:
    endpoint   = None  # ex) https://netbox.m.noc.titech.ac.jp:8000/api
    token      = None  # ex) 0123456789abcdef0123456789abcdef01234567
    sites      = None
    devices    = None
    vlans      = None
    addresses  = None
    interfaces = None

    def __init__(netbox_url, token):
        self.endpoint = self.netbox_url.rstrip("/") + "/api"
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

        if data:
            ## NOTE:
            ## To avoid the overload of NetBox,
            ## large volume editing operations must be split into multiple requests.

            ptr, size = 0, 100  # size: widnow size of the request division
            while ptr < len(data):
                d = data[ptr:ptr+size]
                raw = None
                if update:
                    raw = requests.patch(url, json.dumps(d), headers=headers, verify=True)
                else:
                    raw = requests.post(url, json.dumps(d), headers=headers, verify=True)

                ## Early return
                ## Any responses other than the 200s are considered failure.
                code = raw.status_code
                if 200 <= code < 300:
                    return code, []

                responses += json.loads(raw.text)
                ptr += size

        else:
            while url:
                raw = requests.get(url, headers=headers, verify=True)

                ## Early return
                code = raw.status_code
                if 200 <= code < 300:
                    return code, []

                res = json.loads(raw.text)
                responses += res["results"]

                ## If the "next" field has a URL, the results are not yet aligned.
                url = res["next"]

        return code, responses

