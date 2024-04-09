import numpy as np
from scipy.signal import welch, hilbert

class FeatureExtractor:

    bands = {'delta': (1, 4), 'theta': (4, 8), 'alpha': (8, 12), 'beta': (12, 30), 'low-gamma': (30, 60), 'high-gamma': (60, 100)}

    def __init__(self, p_1, p_2, samplerate=2000):
        self.p_1 = p_1
        self.p_2 = p_2
        self.samplerate = samplerate
        # 频带定义

        self.psd_cache = self._precompute_psd()
        self.plv_cache = self._precompute_plv()
    
    def _precompute_psd(self):
        psd_cache = []
        for segment in self.p_1 + self.p_2:
            segment_psd = []
            for channel_data in segment:
                freqs, psd = welch(channel_data, fs=self.samplerate, nperseg=1024)
                channel_psd = []
                for band_name, band in FeatureExtractor.bands.items():
                    avg_psd = np.mean(psd[(freqs >= band[0]) & (freqs <= band[1])])
                    channel_psd.append(avg_psd)
                segment_psd.append(channel_psd)
            psd_cache.append(segment_psd)
        return psd_cache
    
    def _precompute_plv(self):
        plv_cache = []
        for segment_p1, segment_p2 in zip(self.p_1, self.p_2):
            combined_segments = np.concatenate([segment_p1, segment_p2], axis=0)
            plv_matrix = np.zeros((len(combined_segments), len(combined_segments)))
            for i in range(len(combined_segments)):
                for j in range(i, len(combined_segments)):
                    phase_diff = np.angle(hilbert(combined_segments[i])) - np.angle(hilbert(combined_segments[j]))
                    plv = np.abs(np.sum(np.exp(1j * phase_diff)) / len(phase_diff))
                    plv_matrix[i, j] = plv
                    plv_matrix[j, i] = plv  # PLV是对称的
            plv_cache.append(plv_matrix)
        return plv_cache
    
    def get_PSD(self, channels=[]):
        psd_list = []
        for segment_psd in self.psd_cache:
            feature_vector = [segment_psd[channel] for channel in channels]
            psd_list.append(np.concatenate(feature_vector))
        return psd_list
    
    def get_PLV(self, channels=[]):
        plv_list = []
        for plv_matrix in self.plv_cache:
            selected_plv_matrix = plv_matrix[np.ix_(channels, channels)]
            plv_list.append(selected_plv_matrix)
        return plv_list
