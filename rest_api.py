import bottle
import datetime
import psycopg2

import config
import core


def log_rest_api_request():
    connection = psycopg2.connect(
        f"dbname={config.database_name} user={config.database_user} password={config.database_password}")
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO rest_api_requests (recorded_at, remote_address, url, http_method, request_body) "
        "VALUES (%s, %s, %s, %s, %s)",
        (datetime.datetime.now(), bottle.request.remote_addr, bottle.request.url, bottle.request.method,
         str(bottle.request.json)))
    connection.commit()
    cursor.close()
    connection.close()


def auth():
    def decorator(func):
        def wrapper(*args, **kwargs):
            log_rest_api_request()
            if "user" not in bottle.request.headers:
                return bottle.HTTPResponse(status=400, body={"error": "user was not provided"})
            if "password" not in bottle.request.headers:
                return bottle.HTTPResponse(status=400, body={"error": "password was not provided"})
            else:
                credentials = {"user": bottle.request.headers["user"], "password": bottle.request.headers["password"]}
                if "domain_id" in bottle.request.headers:
                    credentials["domain_id"] = bottle.request.headers["domain_id"]
                if "project_name" in bottle.request.headers:
                    credentials["project_name"] = bottle.request.headers["project_name"]
                keystone_response = core.get_token(**credentials)
                if "error" in keystone_response:
                    return bottle.HTTPResponse(status=503,
                                               body={"error": keystone_response["error"]})
                bottle.request.token = keystone_response["token"]
                return func(*args, **kwargs)
        return wrapper
    return decorator


app = bottle.Bottle()


@app.get('/api/token')
@auth()
def get_token():
    return bottle.HTTPResponse(body={"token": bottle.request.token})


@app.get('/api/flavors')
@auth()
def get_flavors():
    result = core.get_flavors(token=bottle.request.token)
    return bottle.HTTPResponse(status=result["status"], body=result["data"])


@app.get('/api/images')
@auth()
def get_images():
    result = core.get_images(token=bottle.request.token)
    return bottle.HTTPResponse(status=result["status"], body=result["data"])


@app.get('/api/networks')
@auth()
def get_networks():
    result = core.get_networks(token=bottle.request.token)
    return bottle.HTTPResponse(status=result["status"], body=result["data"])


@app.get('/api/virtual_machines')
@auth()
def get_virtual_machines():
    result = core.get_virtual_machines(token=bottle.request.token)
    return bottle.HTTPResponse(status=result["status"], body=result["data"])


@app.post('/api/virtual_machines')
@auth()
def create_virtual_machine():
    absent_fields = list(filter(lambda required_field: required_field not in bottle.request.json,
                                ["flavor_name", "image_name", "network_id", "virtual_machine_name"]))
    if absent_fields:
        return bottle.HTTPResponse(status=400,
                                   body={"error": f"the following fields were not provided: {absent_fields}"})
    result = core.create_virtual_machine(token=bottle.request.token,
                                         flavor_name=bottle.request.json["flavor_name"],
                                         image_name=bottle.request.json["image_name"],
                                         network_id=bottle.request.json["network_id"],
                                         virtual_machine_name=bottle.request.json["virtual_machine_name"])
    return bottle.HTTPResponse(status=result["status"], body=result["data"])


bottle.run(app, host=config.rest_api_ip, port=config.rest_api_port, debug=config.debug_mode)
