import os

import requests
import json
import hcl
from pathlib import Path
import argparse

with open(f"{Path.home()}/.terraformrc", "r") as fp:
    token = hcl.load(fp)["credentials"]["app.terraform.io"]["token"]

template_var = {
    "data": {
        "type": "vars",
        "attributes": {
            "description": "",
            "hcl": False,
            "sensitive": False
        }
    }
}


def get_variables(workspace: str, org: str):
    workspace = __get_ws(ws_name=workspace, org=org).json()["data"]["id"]
    return requests.get(url="https://app.terraform.io/api/v2/workspaces/{}/vars".format(workspace),
                        headers={"Authorization": "Bearer {}".format(token),
                                 "Content-Type": "application/vnd.api+json"}).json()["data"]


def update_variable(workspace: str, org: str, var: dict):
    workspace = __get_ws(ws_name=workspace, org=org).json()["data"]["id"]
    return requests.patch(url="https://app.terraform.io/api/v2/workspaces/{ws}/vars/{var_id}"
                          .format(ws=workspace, var_id=var["data"]["id"]),
                          headers={"Authorization": "Bearer {}".format(token),
                                   "Content-Type": "application/vnd.api+json"},
                          data=json.dumps(var))


def insert_variable(workspace: str, var: dict):
    return requests.post(url="https://app.terraform.io/api/v2/workspaces/{}/vars".format(workspace),
                         headers={"Authorization": "Bearer {}".format(token),
                                  "Content-Type": "application/vnd.api+json"},
                         data=json.dumps(var))


def __get_ws(ws_name, org):
    res = requests.get(url="https://app.terraform.io/api/v2/organizations/{org}/workspaces/{ws}".format(org=org,
                                                                                                        ws=ws_name),
                       headers={"Authorization": "Bearer {}".format(token),
                                "Content-Type": "application/vnd.api+json"})

    return res


def read_input():
    parser = argparse.ArgumentParser(description='Initialize terraform workspace and add env variables automatically.')

    parser.add_argument('-o', '--organization', nargs=1, type=str, required=True, dest='org',
                        help='Organization to be used.')

    parser.add_argument('-w', '--workspace', nargs=1, type=str, required=True, dest='ws',
                        help='Workspace where the variables will be inserted')

    parser.add_argument('-v', '--var', nargs='*', type=str, required=False, dest='v',
                        help='Non environment variables to be inserted, must be typed in key:value format',
                        default=None)

    args = parser.parse_args()

    org = args.org[0]
    ws = args.ws[0]

    v = args.v

    if v is not None:
        for i in v:
            tmp = i.split(':')
            var_key = tmp[0]
            var_value = tmp[1]
            template_var["data"]["attributes"]["key"] = var_key
            template_var["data"]["attributes"]["value"] = var_value
            template_var["data"]["attributes"]["category"] = "terraform"

            print(template_var)


if __name__ == '__main__':
    read_input()
