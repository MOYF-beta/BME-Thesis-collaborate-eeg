import os
import numpy as np
from scipy.signal import welch
from scipy.signal import hilbert

from get_windows_from_eegbin import get_windows

# 定义频段
freq_bands = {
    'delta': (1, 4),
    'theta': (4, 8),
    'alpha': (8, 13),
    'beta': (13, 30),
    'gamma': (30, 100)
}

def normalize(data):
    mean = np.mean(data, axis=0)
    std = np.std(data, axis=0)
    std[std == 0] = 1  # 避免除零错误
    return (data - mean) / std


def compute_band_power(data, sample_rate):
    n_channel = data.shape[1]
    power = np.zeros((len(freq_bands),n_channel))
    for idx in range(n_channel):
        for band_i ,(band, (low, high)) in enumerate(freq_bands.items()):
            f, Pxx = welch(data[:,idx], sample_rate, nperseg=sample_rate*2)
            idx_band = np.logical_and(f >= low, f <= high)
            power[band_i,idx] = np.sum(Pxx[idx_band])
    return power

def compute_plv(data1, data2):
    n_channels = data1.shape[1]
    plv_matrix = np.zeros((n_channels*2, n_channels*2))

    # Hilbert变换获取瞬时相位
    phase1 = np.angle(hilbert(data1, axis=0))
    phase2 = np.angle(hilbert(data2, axis=0))
    phase = np.hstack([phase1,phase2])
    
    for i in range(n_channels*2):
        for j in range(n_channels*2):
            phase_diff = phase[:, i] - phase[:, j]
            plv = np.abs(np.mean(np.exp(1j * phase_diff)))
            plv_matrix[i, j] = plv

    return plv_matrix

# 主函数
def process_windows(data_dir, sample_rate):
    windows1, windows2 = get_windows(data_dir)

    all_features = []

    for i in range(len(windows1)):
        window1 = normalize(windows1[i])
        window2 = normalize(windows2[i])

        power1 = compute_band_power(window1, sample_rate)
        power2 = compute_band_power(window2, sample_rate)

        plv_matrix = compute_plv(window1, window2)

        features = {
            'power1': power1,
            'power2': power2,
            'plv_matrix': plv_matrix
        }

        all_features.append(features)

    return all_features

if __name__ == '__main__':
    sample_rate = 250  # Hz
    data_raw_path = './data_raw'
    output_path = './dataset'
    for exp in os.listdir(data_raw_path):
        features = process_windows(os.path.join(data_raw_path,exp), sample_rate)

        # 访问数据的例子
        # for feature in features[:3]:
        #     print(f"Power1: {feature['power1']}") #5*8
        #     print(f"Power2: {feature['power2']}") #5*8
        #     print(f"PLV Matrix Shape: {feature['plv_matrix'].shape}") # 16*16

        # 保存数据
        power1_values = [feature['power1'] for feature in features]
        power2_values = [feature['power2'] for feature in features]
        plv_matrices = [feature['plv_matrix'] for feature in features]
        
        np.savez(os.path.join(output_path,exp), 
                power1_values=power1_values, 
                power2_values=power2_values, 
                plv_matrices=plv_matrices)