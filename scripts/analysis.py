import struct
import pandas as pd
import numpy as np

def read_data_from_file(file_path):
    data_list = []
    time_list = []
    
    with open(file_path, 'rb') as f:
        while True:
            # 读取数据（8个int）
            data_bytes = f.read(32)
            if not data_bytes:
                break
            data_values = struct.unpack('<8i', data_bytes)
            data_list.append(data_values)
            
            # 读取时间（1个double）
            time_bytes = f.read(8)  # 8 bytes for double
            if not time_bytes:
                break
            time_value = struct.unpack('<d', time_bytes)[0]
            time_list.append(time_value)
    
    # 将列表转换为 numpy 数组
    data_array = np.array(data_list)
    time_array = np.array(time_list)
    
    valid_len = min(data_array.shape[0], time_array.shape[0])
    return data_array[:valid_len, :], time_array[:valid_len]

# 通道配置
channels = ['F7', 'Oz', 'O1', 'F2', 'C3', 'T7', 'P4', 'T8']

def read_and_convert_to_dataframe(file_path):
    data, time = read_data_from_file(file_path)
    df = pd.DataFrame(data, columns=channels)
    df['time'] = time
    return df

def synchronize_dataframes(df1, df2):
    start_time = max(df1['time'].iloc[0], df2['time'].iloc[0])
    end_time = min(df1['time'].iloc[-1], df2['time'].iloc[-1])

    df1_sync = df1[(df1['time'] >= start_time) & (df1['time'] <= end_time)]
    df2_sync = df2[(df2['time'] >= start_time) & (df2['time'] <= end_time)]

    min_length = min(len(df1_sync), len(df2_sync))
    df1_sync = df1_sync.iloc[:min_length]
    df2_sync = df2_sync.iloc[:min_length]

    return df1_sync, df2_sync

file1 = 'co_1_2/COM3_24_06_09_15_43_49.eegbin'
file2 = 'co_1_2/COM12_24_06_09_15_43_59.eegbin'

df1 = read_and_convert_to_dataframe(file1)
df2 = read_and_convert_to_dataframe(file2)

df1_sync, df2_sync = synchronize_dataframes(df1, df2)

# 删除 time 列
df1_sync = df1_sync.drop(columns=['time'])
df2_sync = df2_sync.drop(columns=['time'])

# 设置采样率和滑动窗口参数
sample_rate = 250  # Hz
window_size = 10 * sample_rate  # 10秒窗口
step_size = sample_rate  # 每1秒移动一次窗口

def sliding_window(dataframe, window_size, step_size):
    data = dataframe.values
    windows = []
    for start in range(0, len(data) - window_size + 1, step_size):
        window = data[start:start + window_size]
        windows.append(window)
    return windows

# 生成滑动窗口的列表
windows1 = sliding_window(df1_sync, window_size, step_size)
windows2 = sliding_window(df2_sync, window_size, step_size)

# 输出部分窗口数据以检查
print(np.array(windows1).shape)
print(np.array(windows2).shape)

np.savez('./windows', windows1=windows1, windows2=windows2)