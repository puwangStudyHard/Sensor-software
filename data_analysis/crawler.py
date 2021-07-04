import requests
import json

url = 'https://api.weather.com/v1/location/EGLC:9:GB/observations/historical.json?apiKey' \
      '=e1f10a1e78da46f5b10a1e78da96f525&units=e&startDate=20210'
temp_list, humidity_list = [], []
temp_path, humidity_path = './temperature.txt', './humidity.txt'

for month in range(2, 5):
    for day in range(1, 29):
        if day < 10:
            cur_url = url + str(month) + '0' + str(day)
        else:
            cur_url = url + str(month) + str(day)
        response = requests.get(cur_url, verify=False)
        data = json.loads(response.text)['observations']
        for idx, item in enumerate(data):
            if idx % 2 == 0:
                temp_list.append(str(int((item['temp'] - 21) // 1.8)))
                humidity_list.append(str(item['rh']))
        # with open(temp_path, 'a+') as f:
        #     f.write(' '.join(temp_list) + '\n')
        # f.close()
        # with open(humidity_path, 'a+') as f:
        #     f.write(' '.join(humidity_list) + '\n')
        temp_list, humidity_list = [], []
