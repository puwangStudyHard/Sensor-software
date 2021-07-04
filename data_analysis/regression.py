import sklearn
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt


def generate_mock_temp(min_temp, max_temp):
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

    poly_reg = Pipeline([
        ("poly", PolynomialFeatures(degree=5)),
        ("std_scaler", StandardScaler()),
        ("lin_reg", LinearRegression())
    ])
    poly_reg.fit(x_train, y_train)
    predict = poly_reg.predict(np.array([i for i in range(24)]).reshape(-1, 1))
    hour_data = list(predict)
    return hour_data


def generate_mock_humidity(max_humidity):
    data_path = './data_analysis/humidity.txt'
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
        if x_raw[i][0] <= max_humidity:
            for idx, value in enumerate(x_raw[i]):
                x.append(idx)
                y.append(value)
    x_train, y_train = np.array(x), np.array(y)
    x_train = x_train.reshape(-1, 1)

    poly_reg = Pipeline([
        ("poly", PolynomialFeatures(degree=5)),
        ("std_scaler", StandardScaler()),
        ("lin_reg", LinearRegression())
    ])
    poly_reg.fit(x_train, y_train)
    predict = poly_reg.predict(np.array([i for i in range(24)]).reshape(-1, 1))
    hour_data = list(predict)
    return hour_data


def plot_data():
    data_path = './temperature.txt'
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
        if 0 <= x_raw[i][0] <= 20:
            for idx, value in enumerate(x_raw[i]):
                x.append(idx)
                y.append(value)
    x_train, y_train = np.array(x), np.array(y)

    fig, ax = plt.subplots()
    for i in range(5):
        ax.plot(x_train[i*24:(i+1)*24], y_train[i*24:(i+1)*24], label='02-0'+str(i+1))

    x_train = x_train.reshape(-1, 1)
    poly_reg = Pipeline([
        ("poly", PolynomialFeatures(degree=4)),
        ("std_scaler", StandardScaler()),
        ("lin_reg", LinearRegression())
    ])
    poly_reg.fit(x_train, y_train)
    predict = poly_reg.predict(np.array([i for i in range(24)]).reshape(-1, 1))
    ax.plot(np.array([i for i in range(24)]), predict, label='fitting curve-04')
    # hour_data = list(predict)
    # return hour_data
    ax.set_xlabel('hour')
    ax.set_ylabel('temperature')
    ax.set_title('sample data')
    ax.legend()
    plt.show()


if __name__ == '__main__':
    plot_data()
