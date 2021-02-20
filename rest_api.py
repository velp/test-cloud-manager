import bottle
import psycopg2
import threading

import config
import core


def log_rest_api_request(request):
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(
            f"dbname={config.database_name} user={config.database_user} password={config.database_password}")
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO rest_api_requests (remote_address, url, http_method, request_body) "
            "VALUES (%s, %s, %s, %s)",
            (request.remote_addr, request.url, request.method, str(request.json)))
        connection.commit()
    except psycopg2.errors.UndefinedTable:
        print("SQL table does not exist")
    finally:
        if connection is not None:
            cursor.close()
            connection.close()


def auth():
    def decorator(func):
        def wrapper(*args, **kwargs):
            log_rest_api_request(request=bottle.request)
            credentials = dict()
            for required in ["user", "password"]:
                if required not in bottle.request.headers:
                    return bottle.HTTPResponse(status=400, body={"error": f"{required} was not provided"})
                credentials[required] = bottle.request.headers[required]
            for additional in ["domain_id", "project_name"]:
                credentials[additional] = bottle.request.headers.get(additional)
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


@app.get('/api/statistics/virtual_machines/number/per_day')
@auth()
def get_virtual_machines_number_per_day():
    result = core.get_virtual_machines_number_per_day()
    if "error" in result:
        return bottle.HTTPResponse(status=503, body=result["error"])
    for item in result["data"]:
        item["timestamp"] = str(item["timestamp"])
    return bottle.HTTPResponse(status=200, body=str(result["data"]))


stats = threading.Thread(target=core.send_statistics, daemon=True)
stats.start()
bottle.run(app, host=config.rest_api_ip, port=config.rest_api_port, debug=config.debug_mode)
