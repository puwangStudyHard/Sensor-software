# Sensor-software
IoT-based sensor application
# Readme

## 代码骨架

```bash
.
├── Readme.md
├── __pycache__  
│   ├── app.cpython-38.pyc
│   └── utils.cpython-38.pyc
├── app.py  
├── config.yaml  # Configuration file, some key constants are defined here
├── data_analysis  # data analysis module
│   ├── __pycache__  # default
│   │   └── regression.cpython-38.pyc
│   ├── crawler.py  
│   ├── daylight.txt  # daylight text file
│   ├── energy.txt  # energy text file
│   ├── humidity.txt  # crawl to get humidity data
│   ├── regression.py  # regression task
│   └── temperature.txt  #crawl to get temperature data
├── sensor-client.py  
├── static  # Front-End static files
│   ├── css
│   │   └── index.css  # css style file
│   ├── data  # This is the automatically generated data of 8 sensors, which will be refreshed every time the user terminal is run
│   │   ├── 1.txt
│   │   ├── 2.txt
│   │   ├── 3.txt
│   │   ├── 4.txt
│   │   ├── 5.txt
│   │   ├── 6.txt
│   │   ├── 7.txt
│   │   ├── 8.txt
│   │   ├── myplot-2.jpg
│   │   ├── myplot-3.jpg
│   │   ├── myplot-4.jpg
│   │   └── myplot-5.jpg
│   ├── img  # Here are some pictures involved in the Front-End page
│   │   ├── ac.png
│   │   ├── bupt_logo.png
│   │   ├── bytedance.png
│   │   ├── ed_logo.png
│   │   ├── favicon.ico
│   │   ├── my_img.jpg
│   │   ├── nice.jpg
│   │   ├── right.png
│   │   ├── small_left.png
│   │   ├── small_right.png
│   │   └── touxiang.jpg
│   └── js  # js library file
│       ├── echarts-template.js
│       ├── echarts.min.js
│       └── jquery-3.5.1.js
├── templates  # Front-End page
│   └── index.html 
└── utils.py  # Tools, place some functions required by the user terminal and sensors

```

## app.py（user terminal）

Main function: Start the Flask service, and establish contact with the remote Broker at the same time, ready to transmit and receive data.

```python
# Start two threads, one is Flask service, the other is MQTT service
try:
    _thread.start_new_thread(start_flask, ("Thread-1", 2,))
    _thread.start_new_thread(start_mqtt, ("Thread-2", 4,))
```

MQTT main part：

```python
# If the data from MQTT is received, write it into a text file (or mysql)
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
```

Flask main part：

```python
# Set index.html as the Front-End display page called by default
@app.route('/')
def hello_world():
    return render_template('index.html')
```

```python
# Get the latest data from the text file to the Front-End
@app.route('/get-param')
def get_param():
    var_type = request.args.get('type')
    data = utils.get_data(var_type, conn)
    return {'data': data}
```

```python
# Take the time-interval submitted by the user from the Front-End and pass it to the sensor client
@app.route('/set-interval')
def set_interval():
    interval = request.args.get('interval')
    interval_type = request.args.get('type')
    data = interval_type + ';' + interval
    client.publish("set-interval", data, qos=2)
    # client.loop_start()
    return "OK"
```

## sensor-client.py(sensor client)

Main function: open 8 threads, representing 8 different sensors

```python
# Define a thread class, each sensor calls this class
class myThread (threading.Thread):
    def __init__(self, thread_id, interval, time_stamp, all_data):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.interval = interval
        self.time_stamp = time_stamp
        self.is_start = False
        self.all_data = all_data
        self.time_frequency = utils.read_from_config('send_frequency')

    def run(self):
        counter = 0
        # The sensor is turned off by default until it receives an instruction from the user terminal 
        while not self.is_start:
            time.sleep(1)
        while self.is_start:
            # Set the default transmission frequency of the sensor (2s)
            self.interval = utils.read_from_config('send_frequency')
            print('self.interval: ', self.interval)
            if counter >= len(self.all_data):
                break
            # sleep 2s
            time.sleep(self.interval)
            # send data to MQTT broker
            payload = str(self.thread_id) + ';' + str(self.time_stamp) + ":" + str(self.all_data[counter])
            client.publish("send-data", payload=payload, qos=2)
            client.loop_start()
            self.time_stamp += self.time_frequency * 60
            counter += self.time_frequency
```

```python
# build 8 threads
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
```


## utils.py

Main functions: read data, process data, generate data

```python
# The get_data function is used to get data from txt or mysql and return it to the Front-End in the form of a dictionary for display
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
                # read one line data
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

    return {
        'title': variable_dic['name'],
        'unit_name': variable_dic['unit_name'],
        'unit': variable_dic['unit'],
        'peak': peak,
        'valley': valley,
        'average': average,
        'series': series[1:],
        'date': date,
        'tableList': table_data[::-1]
    }
```

```python
# Function used to read data from configuration file
def read_from_config(key):
    f = open(config_path, 'r', encoding='utf-8')
    result = f.read()
    config_dic = yaml.load(result, Loader=yaml.FullLoader)
    return config_dic[key]
```

```python
# Generate random temperature data based on polynomial regression and humidity data in the same way
def generate_random_temperature():
    all_temp_data = []
    for i in range(3):
        min_temp = random.randint(2, 10)
        max_temp = random.randint(min_temp + 2, 21)
        # Call the regression function in data_analysis, do a regression to get hourly data
        hour_data = reg.generate_mock_temp(min_temp, max_temp)
        # Randomize hourly data into minute data
        for data in hour_data:
            for _ in range(60):
                bias = (random.randint(0, 7) / 10 - 0.3)
                all_temp_data.append(round(data + bias, 1))
    return all_temp_data
```

```python
# Functions that interact with the database
def connect2mysql():
    mysql_config = read_from_config('mysql')
    conn = pymysql.connect(host=mysql_config['ip'], port=mysql_config['port'], user=mysql_config['username'],
                           password=mysql_config['password'], db=mysql_config['database'], charset='utf8')
    return conn
```

## index.html

main function: Front-End page

```js
// Get the full amount of data from the user terminal and display it on the page in real time
function get_data(){
    let var_type = variable_type
    $.ajax({
        url: '/get-param?type=' + var_type,
        timeout: 10000,
        success: function (data){
            option.yAxis.axisLabel.formatter = "{value}" + data.data.unit + ""
            option.legend.data = data.data.date
            option.title.text = data.data.title
            option.series = []
            for (var i=0; i<data.data.series.length; i++) {
                option.series.push({
                    name: data.data.series[i].name,
                    type: 'line',
                    stack: String(i),
                    data: data.data.series[i].data
                })
            }
            let tableString = '<table border="1" width="80%"><tr style="width:40%"> <th>time</th><th>' + data.data.unit_name + '</th></tr>'
            for (var i=0; i<data.data.tableList.length; i++) {
                tableString += generate_line(data.data.tableList[i], data.data.unit)
            }
            tableString += '</table>'
            // tempChart.clear()
            tempChart.setOption(option)
            // console.log("option: ", option)
            // console.log("series: ", data.data.series)
            $('#peak').html("Peak: " + data.data.peak)
            $('#valley').html("Valley: " + data.data.valley)
            $('#average').html("Average: " + data.data.average)
            $('#data-table').html(tableString)
        }
    })
}
```

```js
// The user sets the time-interval and sends it to the Back-End
function set_interval(var_type) {
    value = document.getElementById('freq').value
    $.ajax({
        url: '/set-interval?type=' + var_type + '&interval=' + value,
        timeout: 10000
    })
    document.getElementById('freq').value = ""
}
```

```html
// body part is the components of whole Front-end page
<body>
    <header id="header">
        <a class="default" id="bupt_logo" href="https://www.manchester.ac.uk/" target="_blank">
            <img style="width:100%;height:100%" src="../static/img/ed_logo.png">
        </a>
    </header>
    <section id="main">
        <div id="link_list">
            <a onclick="change_type(1)" target="_blank"><button class="info_btn">R1 Temp</button></a>&nbsp;
            <a onclick="change_type(2)" target="_blank"><button class="info_btn">R1 Humidity</button></a>&nbsp;
            <a onclick="change_type(3)" target="_blank"><button class="info_btn">R2 Temp</button></a>&nbsp;
            <a onclick="change_type(4)" target="_blank"><button class="info_btn">R2 Humidity</button></a>&nbsp;
            <a onclick="change_type(5)" target="_blank"><button class="info_btn">OD Temp</button></a>&nbsp;
            <a onclick="change_type(6)" target="_blank"><button class="info_btn">OD Humidity</button></a>&nbsp;
            <a onclick="change_type(7)" target="_blank"><button class="info_btn">OD Daylight</button></a>
            <a onclick="change_type(8)" target="_blank"><button class="info_btn">Energy Consumption</button></a>
        </div>
        <div id="key-data">
            <div id="peak">Peak: </div>
            <div id="valley">Valley: </div>
            <div id="average">Average: </div>
            <div id="update-freq">
                Update Time Interval: <input id="freq" style="position:relative;width:60px"/>min/trans
                <button onclick="set_interval(variable_type)">Submit</button>
            </div>
        </div>
        <div id="chart">
            <script>
                var tempChart = echarts.init(document.getElementById("chart"))
                // tempChart.setOption(option)
                setInterval(get_data, 1000)
            </script>
        </div>
        <div id="data-table"></div>
    </section>
</body>
```

## crawler.py

A simple crawler file, crawl the content of the specified URL, do some analysis to extract the temperature and humidity data, and prepare for the subsequent regression task

## regression.py

The regression function is here

```python
# Given a minimum and maximum value (make sure that the data used each time is not exactly the same, otherwise the same curve will be obtained for each regression)
def generate_mock_temp(min_temp, max_temp):
	# read data first
    data_path = './data_analysis/temperature.txt'
    x_raw = []
    with open(data_path, 'r') as f:
        line = f.readline()
        while line:
            cur_data = line[:-1].split(' ')
            x_raw.append([int(x) for x in cur_data])
            line = f.readline()
    f.close()

    x, y = [], []
    for i in range(len(x_raw)):
        if min_temp <= x_raw[i][0] <= max_temp:
            for idx, value in enumerate(x_raw[i]):
                x.append(idx)
                y.append(value)
    x_train, y_train = np.array(x), np.array(y)
    x_train = x_train.reshape(-1, 1)
	
	# Do regression mission here
    poly_reg = Pipeline([
        ("poly", PolynomialFeatures(degree=5)),
        ("std_scaler", StandardScaler()),
        ("lin_reg", LinearRegression())
    ])
    # tting data
    poly_reg.fit(x_train, y_train)
    # Then generate 24 hours of data
    predict = poly_reg.predict(np.array([i for i in range(24)]).reshape(-1, 1))
    hour_data = list(predict)
    return hour_data
```
