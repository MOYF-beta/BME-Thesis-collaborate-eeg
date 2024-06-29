data = [
    {'[1]': 0.46238805970149255, '[2]': 0.39367396593673964, '[3]': 0.669259384511329, '[1, 2]': 0.33580018501387604, '[1, 3]': 0.3494529887426669, '[2, 3]': 0.44892258579409416}
    ,{'[1]': 0.5316417910447762, '[2]': 0.3980535279805353, '[3]': 0.6269868109570511, '[1, 2]': 0.3111933395004625, '[1, 3]': 0.3494529887426669, '[2, 3]': 0.4096169193934557}
    ,{'[1]': 0.46238805970149255, '[2]': 0.672992700729927, '[3]': 0.6574230639161313, '[1, 2]': 0.32580943570767806, '[1, 3]': 0.3494529887426669, '[2, 3]': 0.4866320830007981}
    ,{'[1]': 0.4471641791044776, '[2]': 0.48369829683698295, '[3]': 0.6564085221508286, '[1, 2]': 0.38630897317298796, '[1, 3]': 0.3494529887426669, '[2, 3]': 0.41041500399042297}
    ,{'[1]': 0.45611940298507464, '[2]': 0.13381995133819952, '[3]': 0.6851538721677376, '[1, 2]': 0.48695652173913045, '[1, 3]': 0.3494529887426669, '[2, 3]': 0.44094173982442136}
]

sum_dict = {'[1]': 0, '[2]': 0, '[3]': 0, '[1, 2]': 0, '[1, 3]': 0, '[2, 3]': 0}
count_dict = {'[1]': 0, '[2]': 0, '[3]': 0, '[1, 2]': 0, '[1, 3]': 0, '[2, 3]': 0}
max_dict = {'[1]': 0, '[2]': 0, '[3]': 0, '[1, 2]': 0, '[1, 3]': 0, '[2, 3]': 0}
# 遍历每个字典数据并累加到sum_dict和计数到count_dict
for d in data:
    for key in sum_dict:
        if key in d:
            sum_dict[key] += d[key]
            count_dict[key] += 1
            max_dict[key] = max(d[key],max_dict[key])

# 计算每列的均值
mean_dict = {}
for key in sum_dict:
    mean_dict[key] = sum_dict[key] / count_dict[key]

# 输出结果
for key, value in mean_dict.items():
    print(f"{key} mean,max : {mean_dict[key]},{max_dict[key]}")