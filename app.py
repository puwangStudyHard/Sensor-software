import _thread
import time
from flask import Flask
from flask import render_template
from flask import request
import utils
import paho.mqtt.client as mqtt

app = Flask(__name__, static_folder='./static')
conn = None
file_path = './static/data/'

if utils.read_from_config('use-mysql'):
    conn = utils.connect2mysql()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))


def on_message(client, userdata, msg):
    var_type, value_str = str(msg.payload)[2:-1].split(';')
    time_stamp, value = value_str.split(":")
    data_dic = {
        "var_type": var_type,
        "time_stamp": time_stamp,
        "value": value
    }
    if conn:
        utils.insert2mysql(conn, data_dic)
    with open(file_path + var_type + '.txt', 'a+') as f:
        f.write(value_str + "\n")
    f.close()
    print(msg.topic + " " + str(msg.payload))


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
host_dic = utils.read_from_config('server')
client.connect(host_dic['ip'], host_dic['port'], 600)  # keepalive time interval


def start_flask(thread_name, delay):
    app.run(host='0.0.0.0', port=5555)
    if conn:
        conn.close()


def start_mqtt(thread_name, delay):
    client.subscribe('send-data', qos=2)
    client.loop_start()


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/get-param')
def get_param():
    var_type = request.args.get('type')
    data = utils.get_data(var_type, conn)
    return {'data': data}


@app.route('/set-interval')
def set_interval():
    interval = request.args.get('interval')
    interval_type = request.args.get('type')
    data = interval_type + ';' + interval
    client.publish("set-interval", data, qos=2)
    # client.loop_start()
    return "OK"


if __name__ == '__main__':

    # Remove data before
    for i in range(1, 9):
        with open(file_path + str(i) + '.txt', 'w') as f:
            f.write("")
        f.close()
    if conn:
        utils.delete_all_in_mysql(conn)
    # Set up 2 threads
    try:
        _thread.start_new_thread(start_flask, ("Thread-1", 2,))
        _thread.start_new_thread(start_mqtt, ("Thread-2", 4,))
    except:
        print("Error: Cannot start thread...")
    # Update the transmission frequency of all sensors (2 seconds)
    for i in range(1, 9):
        client.publish("set-interval", str(i) + ";20", qos=2)
    while 1:
        time.sleep(1)

