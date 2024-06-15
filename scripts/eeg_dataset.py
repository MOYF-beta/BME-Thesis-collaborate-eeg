import os
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

class EEG_Dataset(Dataset):
    def __init__(self, path='./dataset'):
        self.data_list = []
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.load_data(path)
        
    def load_data(self, path):
        file_list = [f for f in os.listdir(path) if f.endswith('.npz')]
        co_count = 0
        vs_count = 0
        
        for file_name in file_list:
            file_path = os.path.join(path, file_name)
            data = np.load(file_path)
            
            power1_values = data['power1_values']
            power2_values = data['power2_values']
            plv_matrices = data['plv_matrices']
            
            if 'co' in file_name:
                y = torch.tensor([1, 0], dtype=torch.float32).to(self.device)
                co_count += len(power1_values)
            elif 'vs' in file_name:
                y = torch.tensor([0, 1], dtype=torch.float32).to(self.device)
                vs_count += len(power1_values)
            else:
                assert False, "数据集命名不合法"
                
            for i in range(len(power1_values)):
                power1 = power1_values[i]
                power2 = power2_values[i]
                plv_matrix = plv_matrices[i]
                
                band_power = np.concatenate((power1, power2), axis=1).T  # [16, 5]
                band_power_tensor = torch.tensor(band_power, dtype=torch.float32).to(self.device)
                plv_matrix_tensor = torch.tensor(plv_matrix, dtype=torch.float32).to(self.device)
                
                self.data_list.append(((band_power_tensor, plv_matrix_tensor), y))
        
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
