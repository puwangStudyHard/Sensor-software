import logging
import os
import random
import time
import yaml
from data_analysis import regression as reg
import pymysql
logging.basicConfig(level=logging.DEBUG)

data_dir = './static/data/'
config_path = './config.yaml'


def get_data(var_type, conn=None):
    date_info = {
        'name': '05-09',
        'data': [],
    }

    data_path = data_dir + var_type + '.txt'
    peak, valley, average = 0, 100, 0
    series, date, table_data = [], [], []
    counter = 0
    hour_list = []
    variable_dic = read_from_config('variable_dic')[int(var_type)]

    # Read from MySQL
    if conn:
        rows = get_data_from_mysql(conn, var_type)
        for row in rows:
            if 'time_stamp' not in row:
                logging.info("Cannot parse data from MySQL...")
                break
            time_stamp, value = row['time_stamp'], row['value']

            table_data.append([get_time(time_stamp), str(value)])
            cur_date = get_date(time_stamp)
            cur_hour = get_hour(time_stamp)
            if cur_date not in date:
                series.append(date_info)
                hour_list = []
                date.append(cur_date)
                date_info = {'name': cur_date, 'data': []}
                peak, valley, average, counter = 0, 100, 0, 0

            if value > peak:
                peak = value
            if value < valley:
                valley = value
            average = round((average * counter + value) / (counter + 1), 1)
            if cur_hour not in hour_list:
                date_info['data'].append(value)
                hour_list.append(cur_hour)

            counter += 1
        series.append(date_info)
    # Read sensor data from txt file
    else:
        with open(data_path, 'r') as f:
            line = f.readline()
            while line:
                # 读取一行数据
                time_stamp, data_content = line[:-1].split(':')
                time_stamp, value = int(time_stamp), float(data_content)

                table_data.append([get_time(time_stamp), data_content])

                cur_date = get_date(time_stamp)
                cur_hour = get_hour(time_stamp)
                if cur_date not in date:
                    series.append(date_info)
                    hour_list = []
                    date.append(cur_date)
                    date_info = {'name': cur_date, 'data': []}
                    peak, valley, average, counter = 0, 100, 0, 0

                if value > peak:
                    peak = value
                if value < valley:
                    valley = value
                average = round((average * counter + value) / (counter + 1), 1)
                if cur_hour not in hour_list:
                    date_info['data'].append(value)
                    hour_list.append(cur_hour)

                line = f.readline()
                counter += 1
                if not line:
                    series.append(date_info)

    table_data = table_data[::-1]
    if len(table_data) > 50:
        table_data = table_data[:50]
    return {
        'title': variable_dic['name'],
        'unit_name': variable_dic['unit_name'],
        'unit': variable_dic['unit'],
        'peak': peak,
        'valley': valley,
        'average': average,
        'series': series[1:],
        'date': date,
        'tableList': table_data
    }


# time_string format: 2021-05-11
def set_start_time(time_string="2021-05-09"):
    time_array = time.strptime(time_string + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    # print(time_array)
    time_stamp = int(time.mktime(time_array))
    return time_stamp


def get_time(time_stamp):
    time_array = time.localtime(time_stamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", time_array)


def get_date(time_stamp):
    time_array = time.localtime(time_stamp)
    return time.strftime("%m-%d", time_array)


def get_hour(time_stamp):
    time_array = time.localtime(time_stamp)
    return time.strftime("%H", time_array)


def read_from_config(key):
    f = open(config_path, 'r', encoding='utf-8')
    result = f.read()
    config_dic = yaml.load(result, Loader=yaml.FullLoader)
    return config_dic[key]


def generate_random_temperature():
    all_temp_data = []
    for i in range(3):
        min_temp = random.randint(2, 10)
        max_temp = random.randint(min_temp + 2, 21)
        hour_data = reg.generate_mock_temp(min_temp, max_temp)
        for data in hour_data:
            for _ in range(3600):
                bias = (random.randint(0, 7) / 10 - 0.3)
                all_temp_data.append(round(data + bias, 1))
    return all_temp_data


def generate_random_humidity():
    all_humidity_data = []
    for i in range(3):
        max_temp = random.randint(75, 100)
        hour_data = reg.generate_mock_humidity(max_temp)
        for data in hour_data:
            for _ in range(3600):
                bias = (random.randint(0, 20) / 10 - 1)
                all_humidity_data.append(round(data + bias, 1))
    return all_humidity_data


def generate_random_daylight():
    all_daylight_data = []
    file_path = './data_analysis/daylight.txt'
    hour_data = []
    with open(file_path, 'r') as f:
        line = f.readline()
        while line:
            raw_data = line.split(' ')
            day_data = [int(x) for x in raw_data]
            hour_data += day_data
            line = f.readline()
    for data in hour_data:
        for _ in range(3600):
            bias = (random.randint(0, 100) - 50)
            all_daylight_data.append(data + bias)
    return all_daylight_data


def generate_random_energy():
    all_daylight_data = []
    file_path = './data_analysis/energy.txt'
    hour_data = []
    with open(file_path, 'r') as f:
        line = f.readline()
        while line:
            raw_data = line.split(' ')
            day_data = [int(x) for x in raw_data]
            hour_data += day_data
            line = f.readline()
    for data in hour_data:
        for _ in range(3600):
            bias = random.randint(90, 110)
            all_daylight_data.append(int(data * bias / 100))
    return all_daylight_data


def connect2mysql():
    mysql_config = read_from_config('mysql')
    conn = pymysql.connect(host=mysql_config['ip'], port=mysql_config['port'], user=mysql_config['username'],
                           password=mysql_config['password'], db=mysql_config['database'], charset='utf8')
    return conn


def insert2mysql(conn, data_dic):
    conn.ping(reconnect=True)
    cursor = conn.cursor()
    sql = "insert into sensor_data (sensor_id, time_stamp, value) values (%s, %s, %s)"
    cursor.execute(sql, (data_dic['var_type'], data_dic['time_stamp'], data_dic['value']))
    conn.commit()
    cursor.close()


def delete_all_in_mysql(conn):
    conn.ping(reconnect=True)
    cursor = conn.cursor()
    sql = "delete from sensor_data where id > 0"
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    logging.info("Refresh MySQL successfully...")


def get_data_from_mysql(conn, var_type):
    conn.ping(reconnect=True)
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    sql = "select * from sensor_data where sensor_id = %s"
    cursor.execute(sql, var_type)
    data = cursor.fetchall()
    return data


if __name__ == '__main__':
    # data_list = get_data('1')
    # print(data_list)
    # props = read_from_config('use-mysql')
    # print(props)
    # generate_random_temperature()
    # print(read_from_config("variable_dic")[1]['name'])
    # print(generate_random_humidity())
    # generate_random_daylight()
    conn = connect2mysql()
    get_data_from_mysql(conn, 1)
    conn.close()
