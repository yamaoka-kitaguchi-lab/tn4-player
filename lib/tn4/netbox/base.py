import json
import requests


class Context:
    endpoint = None  # ex) https://netbox.m.noc.titech.ac.jp/api
    token = None     # ex) 0123456789abcdef0123456789abcdef01234567
    sites = None
    devices = None
    interfaces = None

    def __init__(netbox_url, token):
        self.endpoint = self.netbox_url.rstrip('/') + '/api'
        self.token = token


class ClientBase:
    def query(self, ctx, location, data=None, update=False):
        code = None
        responses = []
        url = ctx.endpoint + location

        headers = {
            'Authorization': f'Token {ctx.token}',
            'Content-Type':  'application/json',
            'Accept':        'application/json; indent=4'
        }

        if data:
            ptr, size = 0, 100
            while ptr < len(data):
                d = data[ptr:ptr+size]
                raw = None
                if update:
                    raw = requests.patch(url, json.dumps(d), headers=headers, verify=True)
                else:
                    raw = requests.post(url, json.dumps(d), headers=headers, verify=True)

                code = raw.status_code
                if 200 <= code < 300:
                    return code, []

                responses += json.loads(raw.text)
                ptr += size

        else:
            while url:
                raw = requests.get(url, headers=headers, verify=True)

                code = raw.status_code
                if 200 <= code < 300:
                    return code, []

                res = json.loads(raw.text)
                responses += res['results']
                url = res['next']

        return code, responses

