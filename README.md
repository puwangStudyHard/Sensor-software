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
├── app.py  # 服务器后端
├── config.yaml  # 配置文件，一些关键常量在此定义
├── data_analysis  # 数据分析模块
│   ├── __pycache__  # 默认
│   │   └── regression.cpython-38.pyc
│   ├── crawler.py  # 爬虫系统
│   ├── daylight.txt  # 光照文本
│   ├── energy.txt  # 能量文本
│   ├── humidity.txt  # 湿度文本（爬虫获取）
│   ├── regression.py  # 回归任务（多项式回归）
│   └── temperature.txt  # 温度文本（爬虫获取）
├── sensor-client.py  # 传感器端 （
├── static  # 前端的静态文件
│   ├── css
│   │   └── index.css  # css样式文件
│   ├── data  # 这是自动生成的8个传感器的数据，每次运行服务端会被刷新
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
│   ├── img  # 这是前端页面中涉及到的一些图片
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
│   └── js  # js库文件
│       ├── echarts-template.js
│       ├── echarts.min.js
│       └── jquery-3.5.1.js
├── templates  # 前端页面
│   └── index.html  # 前端页面
└── utils.py  # 工具类，放置服务端和传感器需要的一些函数

```

## app.py（用户终端）

主要功能：启动Flask服务，同时与远程Broker建立联系，随时准备传输与接收数据

```python
# 启用两个线程，一个是Flask服务，一个是MQTT服务
try:
    _thread.start_new_thread(start_flask, ("Thread-1", 2,))
    _thread.start_new_thread(start_mqtt, ("Thread-2", 4,))
```

MQTT关键部分：

```python
# 如果接收到了从MQTT传来的数据，写入文本文件（或mysql）
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

Flask关键部分：

```python
# 将index.html设置为默认调用的前端显示页面
@app.route('/')
def hello_world():
    return render_template('index.html')
```

```python
# 从文本文件里拿最新数据往前端传
@app.route('/get-param')
def get_param():
    var_type = request.args.get('type')
    data = utils.get_data(var_type, conn)
    return {'data': data}
```

```python
# 从前端拿用户提交的time-interval传给传感器端
@app.route('/set-interval')
def set_interval():
    interval = request.args.get('interval')
    interval_type = request.args.get('type')
    data = interval_type + ';' + interval
    client.publish("set-interval", data, qos=2)
    # client.loop_start()
    return "OK"
```

## sensor-client.py

主要功能：开启8个线程，分别代表8个不同的传感器

```python
# 定义一个线程类，每个传感器都调用这个类
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
        # 传感器默认处于关闭状态，直到收到服务端的指令
        while not self.is_start:
            time.sleep(1)
        while self.is_start:
            # 设置传感器的默认传输频率（2s）
            self.interval = utils.read_from_config('send_frequency')
            print('self.interval: ', self.interval)
            if counter >= len(self.all_data):
                break
            # 休眠2s
            time.sleep(self.interval)
            # 向MQTT传输数据
            payload = str(self.thread_id) + ';' + str(self.time_stamp) + ":" + str(self.all_data[counter])
            client.publish("send-data", payload=payload, qos=2)
            client.loop_start()
            self.time_stamp += self.time_frequency * 60
            counter += self.time_frequency
```

```python
# 构造了8个线程
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

主要功能：读取数据、处理数据、生成数据

```python
# get_data函数，用于从txt或mysql中拿数据，并以字典形式返回给前端用于显示
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
# 从配置文件里读数据的函数
def read_from_config(key):
    f = open(config_path, 'r', encoding='utf-8')
    result = f.read()
    config_dic = yaml.load(result, Loader=yaml.FullLoader)
    return config_dic[key]
```

```python
# 生成基于多项式回归的随机的温度数据、湿度数据同理
def generate_random_temperature():
    all_temp_data = []
    for i in range(3):
        min_temp = random.randint(2, 10)
        max_temp = random.randint(min_temp + 2, 21)
        # 调用data_analysis里的回归文件，作一次回归拿到每小时的数据
        hour_data = reg.generate_mock_temp(min_temp, max_temp)
        # 把小时数据随机成分钟数据
        for data in hour_data:
            for _ in range(60):
                bias = (random.randint(0, 7) / 10 - 0.3)
                all_temp_data.append(round(data + bias, 1))
    return all_temp_data
```

```python
# 后缀为mysql都是与数据库交互的函数
def connect2mysql():
    mysql_config = read_from_config('mysql')
    conn = pymysql.connect(host=mysql_config['ip'], port=mysql_config['port'], user=mysql_config['username'],
                           password=mysql_config['password'], db=mysql_config['database'], charset='utf8')
    return conn
```

## index.html

主要功能：前端页面

```js
// 从服务器端拿到全量数据并实时显示在页面上
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
// 用户设置了time-interval后传会服务器端
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
// body部分是整个前端的组件
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

简单的爬虫文件，爬取制定url的内容，作一些解析提取出温度和湿度数据，为后面的回归任务做准备

## regression.py

回归函数放在这里

```python
# 给定一个最小值和最大值（确保每次使用的数据都不完全相同，否则每次回归得到的是相同的曲线）
def generate_mock_temp(min_temp, max_temp):
	# 先读取数据
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
	
	# 在这里进行回归任务
    poly_reg = Pipeline([
        ("poly", PolynomialFeatures(degree=5)),
        ("std_scaler", StandardScaler()),
        ("lin_reg", LinearRegression())
    ])
    # 拟合
    poly_reg.fit(x_train, y_train)
    # 然后生成24小时的数据
    predict = poly_reg.predict(np.array([i for i in range(24)]).reshape(-1, 1))
    hour_data = list(predict)
    return hour_data
```
