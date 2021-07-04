import _thread
import logging
import random
import threading
import paho.mqtt.client as mqtt
import time
import utils
import data_analysis.regression as reg

logging.basicConfig(level=logging.DEBUG)


class myThread (threading.Thread):
    def __init__(self, thread_id, interval, time_stamp, all_data):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.interval = interval
        self.time_stamp = time_stamp
        self.is_start = False
        self.all_data = all_data
        self.time_frequency = utils.read_from_config('variable_dic')[thread_id]['time_interval']

    def run(self):
        counter = 0
        while not self.is_start:
            time.sleep(1)
        while self.is_start:
            if counter * self.time_frequency >= len(self.all_data):
                break
            time.sleep(self.interval)
            payload = str(self.thread_id) + ';' + str(self.time_stamp) + ":" + str(self.all_data[counter * self.time_frequency])
            client.publish("send-data", payload=payload, qos=2)
            client.loop_start()
            self.time_stamp += self.time_frequency * 60
            counter += 1


def on_connect(client, userdata, flags, rc):
    logging.info("Connected to the mqtt server successfully, result code: " + str(rc))


def on_message(client, userdata, msg):
    global thread_lake
    if not r1_temp_thread.is_start:
        for thread in thread_lake:
            thread.is_start = True

    var_type, value = str(msg.payload)[2:-1].split(';')
    var_type, value = int(var_type), float(value)
    thread_lake[var_type-1].interval = value
    logging.info(msg.topic + " " + str(msg.payload) + " " + utils.read_from_config("variable_dic")[var_type]['name'])


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
host_dic = utils.read_from_config('server')
client.connect(host_dic['ip'], host_dic['port'], 600)  # 600为keepalive的时间间隔


def send_data():
    temp = generate_random_temperature()
    client.publish('fifa', payload='1;' + str(temp), qos=2)
    client.loop_start()


def start_mqtt(threadName):
    client.subscribe('set-interval', qos=2)
    client.loop_start()


def generate_random_data(var_type):
    if var_type == 1:
        return generate_random_temperature()
    else:
        return generate_random_humidity()


def generate_random_temperature():
    min_temp = random.randint(0, 15)
    max_temp = random.randint(min_temp, 21)
    hour_data = reg.generate_mock_temp(min_temp, max_temp)
    print(hour_data)
    return hour_data


def generate_random_humidity():
    humidity = random.randint(20, 50)
    return humidity


if __name__ == '__main__':
    time_stamp = utils.set_start_time(time_string=utils.read_from_config('start_date'))
    # 1. R1_TEMP
    r1_temp_thread = myThread(1, 1000, time_stamp, utils.generate_random_temperature())
    # 2. R1_HUMIDITY
    r1_humidity_thread = myThread(2, 1000, time_stamp, utils.generate_random_humidity())
    # 3. R2_TEMP
    r2_temp_thread = myThread(3, 1000, time_stamp, utils.generate_random_temperature())
    # 4. R2_HUMIDITY
    r2_humidity_thread = myThread(4, 1000, time_stamp, utils.generate_random_humidity())
    # 5. OD_TEMP
    od_temp_thread = myThread(5, 1000, time_stamp, utils.generate_random_temperature())
    # 6. OD_HUMIDITY
    od_humidity_thread = myThread(6, 1000, time_stamp, utils.generate_random_humidity())
    # 7. DAYLIGHT
    daylight_thread = myThread(7, 1000, time_stamp, utils.generate_random_daylight())
    # 8. ENERGY
    energy_thread = myThread(8, 1000, time_stamp, utils.generate_random_energy())

    thread_lake = [r1_temp_thread, r1_humidity_thread, r2_temp_thread, r2_humidity_thread,
                   od_temp_thread, od_humidity_thread, daylight_thread, energy_thread]
    for thread in thread_lake:
        thread.start()
    _thread.start_new_thread(start_mqtt, ("Thread-2",))
