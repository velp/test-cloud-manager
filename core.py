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

    keystone_response = requests.post(f"http://{config.openstack_ip}/identity/v3/auth/tokens?nocatalog", json=data)
    token = error = str()
    if keystone_response.status_code != 201:
        error = f"keystone error: {keystone_response.text}"
    else:
        token = keystone_response.headers["X-Subject-Token"]
    return {
        "status": keystone_response.status_code,
        "error": error,
        "token": token
    }
