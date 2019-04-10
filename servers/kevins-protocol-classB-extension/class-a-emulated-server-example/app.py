from flask import Flask, request
from fwtransfer.fwtransfer import KPAdaptedClassB
import json
import time
import sys

app = Flask(__name__)

update_length = None

try:
    update_length = int(sys.argv[1])
except IndexError as e:
    print("USING FULL UPDATE")


with open('update_contents.hex') as f:
    contents = f.readlines()
    contents = "".join(contents)
    contents = contents.replace("\n", "")
    if update_length is not None:
        contents = contents[:update_length * 2]

update = KPAdaptedClassB(contents, logger_file="500_class_a_1.txt")
start_time = time.asctime(time.localtime(time.time()))


@app.route("/uplink", methods=["POST"])
def on_uplink():
    print("UL RECEIVED...")
    uplink_data = json.loads(request.data.decode("utf-8"))
    uplink_contents = uplink_data["hex"]
    if uplink_contents == "0000":
        pkts_as_bytearr = update.start_update()
        return bytes(pkts_as_bytearr)
    else:
        if update.check_acks(uplink_contents):
            pkts_as_bytearr = update.next()
            bytes_to_send = bytes(pkts_as_bytearr)
            return bytes_to_send
        else:
            return ""


if __name__ == "__main__":
    app.run("localhost", port=5000)
