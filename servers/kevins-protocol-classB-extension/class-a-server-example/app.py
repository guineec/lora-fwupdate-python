import atexit
from flask import Flask, jsonify, request
from dass.api import ApiInstance
from fwtransfer.fwtransfer import KPAdaptedClassB
import base64
import sys

update_length = int(sys.argv[1])

app = Flask(__name__)
api = ApiInstance("tcd_cianguinee", "cian1234")
with open('update_contents.hex') as f:
    contents = f.readlines()
    contents = "".join(contents)
    contents = contents.replace("\n", "")
    if update_length is not None:
        contents = contents[:update_length * 2]

dev_eui = '70b3d599e0010262'
update = KPAdaptedClassB(contents, dev_eui, api, 180, num_rx_windows=1)

api.register_callback_url('http://34.240.71.240/')
# Ensure API Callbacks deregistered on exit
atexit.register(api.deregister_callback_url)

# Finally, start the update
update.start_update()
# update.next()


@app.route("/", methods=["GET"])
def index():
    return jsonify({"hello": "world"})


@app.route("/rest/callback/payloads/ul", methods=["POST"])
def uplink():
    uplink_contents = request.json["dataFrame"]
    uplink_contents = base64.b64decode(uplink_contents).hex()
    if update.check_acks(uplink_contents):
        update.next()
        print("NEXT CALLED")
    else:
        print("UPDATE FINISHED")
    return ""


if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)
