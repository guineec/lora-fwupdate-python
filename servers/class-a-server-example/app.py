import atexit
from flask import Flask, jsonify, request
from dass.api import ApiInstance
from fwtransfer.fwtransfer import ClassBFWUpdate

app = Flask(__name__)
api = ApiInstance("tcd_cianguinee", "cian1234")
with open('update_contents.hex') as f:
    contents = f.readlines()
    contents = "".join(contents)
    contents = contents.replace("\n", "")

api.register_callback_url("http://63.35.236.177/")

dev_eui = '70b3d599e0010262'
update = ClassBFWUpdate(contents, dev_eui, api, 180, num_rx_windows=1)

api.register_callback_url('http://63.35.236.177/')
# Ensure API Callbacks deregistered on exit
atexit.register(api.deregister_callback_url)

# Finally, start the update
update.start_update()


@app.route("/", methods=["GET"])
def index():
    return jsonify({"hello": "world"})


@app.route("/rest/callback/payloads/ul", methods=["POST"])
def uplink():
    print("UL " + str(dir(request)))
    return ""


if __name__=="__main__":
    app.run(host="0.0.0.0", port=80)
