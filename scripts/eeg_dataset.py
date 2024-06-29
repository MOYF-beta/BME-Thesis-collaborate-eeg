import os
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

class EEG_Dataset(Dataset):
    def __init__(self, path='./dataset',dispose = 0,specific_file = None,symmetry = False):
        self.data_list = []
        self.dispose = dispose
        self.symmetry = symmetry
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.specific_file = specific_file
        self.load_data(path)
        
        
        
        
    def load_data(self, path):
        file_list = [f for f in os.listdir(path) if f.endswith('.npz')]
        file_list = file_list if self.specific_file is None else self.specific_file
        co_count = 0
        vs_count = 0
        
        for file_name in file_list:
            file_path = os.path.join(path, file_name)
            data = np.load(file_path)
            
            power1_values = data['power1_values']
            power2_values = data['power2_values']
            plv_matrices = data['plv_matrices']
            
            nan_data = 0
            if 'co' in file_name:
                y = torch.tensor([0.6, 0.4], dtype=torch.float32).to(self.device)
                co_count += len(power1_values)
            elif 'vs' in file_name:
                y = torch.tensor([0.4, 0.6], dtype=torch.float32).to(self.device)
                vs_count += len(power1_values)
            else:
                assert False, "数据集命名不合法"
            
            # Combine all data into a single list for shuffling
            combined_data = list(zip(power1_values, power2_values, plv_matrices))
            if self.symmetry:
                combined_data = combined_data +  list(zip(power2_values, power1_values, plv_matrices.transpose(0,2,1)))
            
            # Randomly shuffle the combined data
            np.random.shuffle(combined_data)
            
            # Calculate the number of data points to retain
            retain_count = int((1 - self.dispose) * len(combined_data))
            
            # Retain the required number of data points
            retained_data = combined_data[:retain_count]
            
            for power1, power2, plv_matrix in retained_data:
                band_power = np.concatenate((power1, power2), axis=1).T  # [16, 5]
                band_power_tensor = torch.tensor(band_power, dtype=torch.float32).to(self.device)
                plv_matrix_tensor = torch.tensor(plv_matrix, dtype=torch.float32).to(self.device)
                
                if not torch.any(torch.isnan(band_power_tensor)) and not torch.any(torch.isnan(plv_matrix_tensor)):
                    self.data_list.append(((band_power_tensor, plv_matrix_tensor), y))
                else:
                    nan_data += 1
            
            if nan_data != 0:
                print(f'warning:{nan_data} data point is nan')
        
        print(f"Loaded files: {file_list}")
        print(f"Total entries: {len(self.data_list)}")
        print(f"co count: {co_count}")
        print(f"vs count: {vs_count}")

    def __len__(self):
        return len(self.data_list)
    
    def __getitem__(self, idx):
        return self.data_list[idx]

if __name__ == '__main__':
    dataset = EEG_Dataset(path='./dataset')
    batch_size = 4
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    for batch in dataloader:
        (band_power_tensors, plv_matrix_tensors), labels = batch
        print(band_power_tensors.shape)  # (batch_size, 16, 5)
        print(plv_matrix_tensors.shape)  # (batch_size, H, W)
        print(labels.shape)              # (batch_size, 2)
