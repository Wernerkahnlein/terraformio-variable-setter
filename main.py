import requests
import json
import hcl
from pathlib import Path

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
    return requests.get(url="https://app.terraform.io/api/v2/organizations/{org}/workspaces/{ws}".format(org=org,
                                                                                                         ws=ws_name),
                        headers={"Authorization": "Bearer {}".format(token),
                                 "Content-Type": "application/vnd.api+json"})


def read_input():
    with open("vars.json", "r") as payload:
        body = json.loads(payload.read())
        for i in body:
            if i == "constanttypes_staging":
                org = body[i]["organization"]
                ws = body[i]["workspace"]
                for j in body[i]["vars"]:
                    template_var["data"]["attributes"]["key"] = j["key"]
                    template_var["data"]["attributes"]["value"] = j["value"]
                    template_var["data"]["attributes"]["category"] = "env" if j["is_env"] else "terraform"

                    res = insert_variable(var=template_var,
                                          workspace=__get_ws(ws_name=ws, org=org).json()["data"]["id"])

                    if res.status_code == 422:
                        print("Found repeated variable key: {}".format(j["key"]))
                        all_vars = get_variables(org=org, workspace=ws)
                        for var in all_vars:
                            if var["attributes"]["key"] == j["key"] and var["attributes"]["value"] != j["value"]:
                                print("Updating variable: {}....".format(j["key"]))
                                template_var["data"]["id"] = var["id"]
                                res = update_variable(workspace=ws, org=org, var=template_var)
                                print("Succesfully updated variable.") if res.status_code == 200 \
                                    else print("Error updating variable: {}.".format(res.text))
                                template_var.pop("id", None)

                    if res.status_code == 201:
                        print("Succesfully inserted variable: {}".format(j["key"]))


if __name__ == '__main__':
    # get_variables(workspace="tf-digidolar-languages-staging", org="bvi-wallenomic")
    read_input()
