EPOCHS = 20
LR = 1e-3
TRAIN_DISPOSE_LIST = [0.1, 0.5, 0.8, 0.9, 0.95, 0.99]# 值越大扔的数据越多

from model import Model, device
from eeg_dataset import EEG_Dataset
from torch.utils.data import DataLoader
from NN_train import train

def main_test_dispose():
    train_batch_size = 5
    val_batch_size = 20
    val_dataset = EEG_Dataset(path='./dataset')

    for dispose_value in TRAIN_DISPOSE_LIST:
        print(f"Training with dispose value: {dispose_value}")
        train_dataset = EEG_Dataset(path='./dataset', dispose=dispose_value)
        
        train_loader = DataLoader(train_dataset, batch_size=train_batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=val_batch_size, shuffle=False)
        
        model = Model(8, 5, PSD_en=True, PLV_en=True).to(device)
        train(model, train_loader, val_loader, dispose_value,EPOCHS,LR,True,True)
        model = Model(8, 5, PSD_en=False, PLV_en=True).to(device)
        train(model, train_loader, val_loader, dispose_value,EPOCHS,LR,False,True)
        model = Model(8, 5, PSD_en=True, PLV_en=False).to(device)
        train(model, train_loader, val_loader, dispose_value,EPOCHS,LR,True,False)


if __name__ == '__main__':
    main_test_dispose()
