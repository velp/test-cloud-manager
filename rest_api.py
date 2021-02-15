import bottle

import core

app = bottle.Bottle()


def auth():
    def decorator(func):
        def wrapper(*args, **kwargs):
            if "user" not in bottle.request.headers:
                return bottle.HTTPResponse(status=400, body={"error": "user was not provided"})
            if "password" not in bottle.request.headers:
                return bottle.HTTPResponse(status=400, body={"error": "password was not provided"})
            else:
                credentials = {"user": bottle.request.headers["user"], "password": bottle.request.headers["password"]}
                if "domain_id" in bottle.request.headers:
                    credentials["domain_id"] = bottle.request.headers["domain_id"]
                keystone_response = core.get_token(**credentials)
                if "error" in keystone_response:
                    return bottle.HTTPResponse(status=keystone_response["status"],
                                               body={"error": keystone_response["error"]})
                bottle.request.token = keystone_response["token"]
                return func(*args, **kwargs)
        return wrapper
    return decorator


@app.route('/api/token')
@auth()
def get_token():
    return bottle.HTTPResponse(body={"token": bottle.request.token})


@app.route('/api/flavors')
def get_flavors():
    pass


bottle.run(app, host="192.168.0.104", port=8081, debug=True)
