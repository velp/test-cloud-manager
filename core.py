import requests

import config


def get_token(user, password, domain_id="default"):
    data = {
        "auth": {
            "identity": {
                "methods": ["password"],
                "password": {
                    "user": {
                        "name": user,
                        "domain": {"id": domain_id},
                        "password": password
                    }
                }
            }
        }
    }
    result = dict()
    try:
        keystone_response = requests.post(url=f"http://{config.openstack_ip}/identity/v3/auth/tokens?nocatalog",
                                          json=data)
    except requests.exceptions.ConnectionError:
        result["error"] = f"keystone is not available."
    else:
        if keystone_response.status_code != 201:
            result["error"] = f"keystone error: {keystone_response.text}"
        else:
            result["token"] = keystone_response.headers["X-Subject-Token"]
    return result


def get_flavors(token):
    response = requests.get(url=f"http://{config.openstack_ip}/compute/v2.1/flavors/detail",
                            headers={"X-Auth-Token": token})
    return {"status": response.status_code, "data": response.json()}


def get_images(token):
    response = requests.get(url=f"http://{config.openstack_ip}/image/v2/images", headers={"X-Auth-Token": token})
    return {"status": response.status_code, "data": response.json()}


def get_networks(token):
    response = requests.get(url=f"http://{config.openstack_ip}:9696/v2.0/networks", headers={"X-Auth-Token": token})
    return {"status": response.status_code, "data": response.json()}


def get_virtual_machines(token):
    response = requests.get(url=f"http://{config.openstack_ip}/compute/v2.1/servers/detail",
                            headers={"X-Auth-Token": token})
    return {"status": response.status_code, "data": response.json()}


def create_virtual_machine(token, flavor_name, image_name, network_id, virtual_machine_name):
    all_flavors = get_flavors(token)
    if all_flavors["status"] != 200:
        return {"status": all_flavors["status"], "error": f"get flavor list error: {all_flavors['error']}"}
    flavor_ref = None
    for flavor_item in all_flavors["data"]["flavors"]:
        if flavor_item["name"] == flavor_name:
            flavor_ref = flavor_item["id"]
            break
    if flavor_ref is None:
        return {"status": 404, "error": f"flavor {flavor_name} not found"}

    all_images = get_images(token)
    if all_images["status"] != 200:
        return {"status": all_images["status"], "error": f"get image list error: {all_images['error']}"}
    image_ref = None
    for image_item in all_images["data"]["images"]:
        if image_item["name"] == image_name:
            image_ref = image_item["id"]
            break
    if image_ref is None:
        return {"status": 404, "error": f"image {image_name} not found"}
    response = requests.post(url=f"http://{config.openstack_ip}/compute/v2.1/servers",
                             headers={"X-Auth-Token": token},
                             json={"server": {
                                 "name": virtual_machine_name,
                                 "imageRef": image_ref,
                                 "flavorRef": flavor_ref,
                                 "min_count": 1,
                                 "max_count": 1,
                                 "networks": [{"uuid": network_id}]
                                }
                             })
    return {"status": response.status_code, "data": response.json()}
