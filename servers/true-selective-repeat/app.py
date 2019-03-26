from flask import Flask, request, Response
from fwtransfer.fwtransfer import TrueSelectiveRepeat
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

update = TrueSelectiveRepeat(contents, num_rx_windows=20)
start_time = time.asctime(time.localtime(time.time()))


@app.route("/uplink", methods=["POST"])
def on_uplink():
    print("UL RECEIVED...")
    uplink_data = json.loads(request.data.decode("utf-8"))
    uplink_contents = uplink_data["hex"]
    if uplink_contents == "0000":
        pkts_as_bytearr = update.start_update()
        bytes_to_send = bytes(pkts_as_bytearr)
        return Response(bytes_to_send, mimetype="application/octet-stream")
    else:
        if update.check_acks(uplink_contents):
            pkts_as_bytearr = update.next()
            bytes_to_send = bytes(pkts_as_bytearr)
            return bytes_to_send
        else:
            print("|---------------- UPDATE FINISHED ----------------|")
            end_time = time.asctime(time.localtime(time.time()))
            print("Started: " + start_time)
            print("Ended: " + end_time)
            retransmits = update.tx_total - (int(len(update.update_segments) / 20) - 1)
            print("Transmitted: " + str(update.tx_total) + " packets in total.")
            print("Retransmits: " + str(retransmits) + " packets.")
            print("Total packet loss percentage: " + str((retransmits / update.pkts_sent) * 100) + "%")
            print("Ineffective uplinks: " + str(retransmits + 1))  # First uplink is always ineffective
            print("|-------------------------------------------------|")
            return ""


if __name__ == "__main__":
    app.run("localhost", port=5002)
