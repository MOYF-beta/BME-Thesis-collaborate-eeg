import numpy as np
from scipy.signal import welch
from scipy.signal import hilbert
from numba import jit

# 定义频段
freq_bands = {
    'delta': (1, 4),
    'theta': (4, 8),
    'alpha': (8, 13),
    'beta': (13, 30),
    'gamma': (30, 100)
}

# 读取数据
def load_windows_from_file(file_path):
    loaded_data = np.load(file_path)
    windows1 = loaded_data['windows1']
    windows2 = loaded_data['windows2']
    return windows1, windows2

def normalize(data):
    return (data - np.mean(data, axis=0)) / np.std(data, axis=0)

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
def process_windows(file_path, sample_rate):
    windows1, windows2 = load_windows_from_file(file_path)

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

file_path = 'windows.npz'
output_path = 'features.npz'
sample_rate = 250  # Hz
features = process_windows(file_path, sample_rate)

# 输出检查
for feature in features[:3]:
    print(f"Power1: {feature['power1']}")
    print(f"Power2: {feature['power2']}")
    print(f"PLV Matrix Shape: {feature['plv_matrix'].shape}")

power1_values = [feature['power1'] for feature in features]
power2_values = [feature['power2'] for feature in features]
plv_matrices = [feature['plv_matrix'] for feature in features]

np.savez(output_path, 
         power1_values=power1_values, 
         power2_values=power2_values, 
         plv_matrices=plv_matrices)