import atexit
from flask import Flask, jsonify
from dass.api import ApiInstance
from fwtransfer.fwtransfer import ClassBFWUpdate

app = Flask(__name__)
api = ApiInstance("tcd_cianguinee", "cian1234")
with open('update_contents.hex') as f:
    contents = f.readlines()
    contents = "".join(contents)
    contents = contents.replace("\n", "")

dev_eui = '70b3d599e0010262'
update = ClassBFWUpdate(contents, dev_eui, api, 180, num_rx_windows=1)

# Ensure API Callbacks deregistered on exit
atexit.register(api.deregister_callback_url)

@app.route("/ack", methods=["POST"])
def ack():
    # TODO