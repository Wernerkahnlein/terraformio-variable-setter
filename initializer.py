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
    return requests.patch(url="https://app.terraform.io/api/v2/workspaces/{ws}/vars/{var_id}".format(ws=workspace,
                                                                                                     var_id=var["data"][
                                                                                                         "id"]),
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
                        help='Organization where the variables will be deployed')

    parser.add_argument('-w', '--workspace', nargs=1, type=str, required=True, dest='ws',
                        help='Workspace where the variables will be deployed')

    args = parser.parse_args()

    org = args.org[0]
    ws = args.ws[0]

    print(f'The organization you selected is: {org}')
    print(f'The organization you selected is: {ws}')

    env_vars = {'AWS_ACCESS_KEY_ID': os.environ.get('AWS_ACCESS_KEY_ID'),
                'AWS_SECRET_ACCESS_KEY': os.environ.get('AWS_SECRET_ACCESS_KEY')}

    for i in env_vars:

        template_var["data"]["attributes"]["key"] = i
        template_var["data"]["attributes"]["value"] = env_vars[i]
        template_var["data"]["attributes"]["category"] = "env"

        res = insert_variable(var=template_var,
                              workspace=__get_ws(ws_name=ws, org=org).json()["data"]["id"])

        if res.status_code == 201:
            print("Succesfully inserted variable: {}".format(i))

        elif res.status_code == 422:
            print("Already inserted variable: {}".format(i))

        else:
            print(res)


if __name__ == '__main__':
    read_input()
