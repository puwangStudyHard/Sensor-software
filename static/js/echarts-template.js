
var option = {
    title: {
        text: 'temp_r1',
        textStyle: {
            color: 'aqua'
        }
    },
    tooltip: {
        trigger: 'axis'
    },
    legend: {
        data: ['05-09', '05-10'],
        textStyle: {
            color: 'aqua'
        }
    },
    grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
    },
    toolbox: {
        feature: {
            saveAsImage: {}
        }
    },
    textStyle: {
        color: 'aqua'
    },
    xAxis: {
        type: 'category',
        boundaryGap: false,
        data: ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11',
            '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']
    },
    yAxis: {
        type: 'value',
        axisLabel: {
            formatter: '{value}℃'
        },
    },
    series: [
        {
            name: '05-09',
            type: 'line',
            stack: '总量1',
            data: [14, 14, 13, 13, 12, 11, 11, 12, 14, 14, 15, 16, 16, 17, 18 ,18, 19]
        },
        {
            name: '05-10',
            type: 'line',
            stack: '总量2',
            data: [12, 11, 10, 8]
        },
    ]
};
