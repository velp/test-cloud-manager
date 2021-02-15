import bottle
import json

import core

app = bottle.Bottle()


@app.route('/api/token')
def token():
    if "user" not in bottle.request.headers:
        return bottle.HTTPResponse(status=400, body={"error": "user was not provided", "token": str()})
    if "password" not in bottle.request.headers:
        return bottle.HTTPResponse(status=400, body={"error": "password was not provided", "token": str()})
    kwargs = {"user": bottle.request.headers["user"], "password": bottle.request.headers["password"]}
    if "domain_id" in bottle.request.headers:
        kwargs["domain_id"] = bottle.request.headers["domain_id"]
    result = core.get_token(**kwargs)
    return bottle.HTTPResponse(status=result["status"],
                               body=json.dumps({"token": result["token"], "error": result["error"]}))


bottle.run(app, host="192.168.0.104", port=8081, debug=True, reloader=True)
