import json
import os
import requests


class Context:
    endpoint    = None  # ex) https://netbox.m.noc.titech.ac.jp:8000
    token       = None  # ex) 0123456789abcdef0123456789abcdef01234567
    sites       = None
    devices     = None
    vlans       = None
    addresses   = None
    prefixes    = None
    fhrp_groups = None
    interfaces  = None

    devices_by_hostname = None

    def __init__(self, endpoint=None, token=None):
        self.endpoint = endpoint.rstrip("/")
        if self.endpoint[:4] != "/api":
            self.endpoint += "/api"
        self.token = token


class ClientBase:
    def query(self, ctx, location, data=None, update=False, delete=False):
        code = None
        responses = []
        url = ctx.endpoint + location

        headers = {
            "Authorization": f"Token {ctx.token}",
            "Content-Type":  "application/json",
            "Accept":        "application/json; indent=4"
        }

        if data is None:
            if delete:
                raw  = requests.delete(url, headers=headers, verify=True)
                code = raw.status_code
                return code  # early return

            while url:
                raw = requests.get(url, headers=headers, verify=True)

                code = raw.status_code
                if not 200 <= code < 300:
                    return [], code  # early return

                res = json.loads(raw.text)
                responses += res["results"]

                ## If the "next" field has a URL, the results are not yet aligned.
                url = res["next"]

            self.dump(location, responses)

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
                    return [], code  # early return

                responses += json.loads(raw.text)
                ptr += size

        return responses, code


    @staticmethod
    def lookup_cache_file(location):
        ## If the response is from /dcim/interfaces/ then it is be exported as dcim-interfaces.cache
        cache_name = "-".join([i for i in location.split("/") if i != ""]) + ".cache"
        cache_dir = os.path.expanduser("~") + "/.cache/tn4-player"
        return cache_name, cache_dir, cache_dir + "/" + cache_name


    def dump(self, location, responses):
        if len(responses) == 0: return  # early return

        _, cache_dir, cache_path = self.lookup_cache_file(location)
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_path, "w") as fd:
            json.dump(responses, fd, indent=4, sort_keys=True, ensure_ascii=False)


    def load(self, location):
        _, _, cache_path = self.lookup_cache_file(location)
        responses, ok = None, True
        try:
            with open(cache_path) as fd:
                responses = json.load(fd)
        except Exception as e:
            ok = False
        return responses, ok
