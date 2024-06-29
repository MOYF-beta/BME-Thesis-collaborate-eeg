EPOCHS = 20
LR = 1e-3


import os
import re
from model import Model, device
from eeg_dataset import EEG_Dataset
from torch.utils.data import DataLoader
from NN_train import train

def main_test_dispose():
    train_batch_size = 5
    val_batch_size = 20
    val_dataset = EEG_Dataset(path='./dataset')
    TRAIN_DISPOSE_LIST = [0.1, 0.5, 0.8, 0.9, 0.95, 0.99]# 值越大扔的数据越多
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

def main_test_cross_ds():

    train_batch_size = 5
    dispose_value = 0.5
    val_batch_size = 20
    
    
    def ds_train(exclude):


        train_files = []
        eval_files = []
        npz_files = [f for f in os.listdir('./dataset') if f.endswith('.npz')]
            
        for npz_file in npz_files:
            num = int(npz_file[3])
            if num not in exclude:
                train_files.append(npz_file)
            else:
                eval_files.append(npz_file)
    
        train_dataset = EEG_Dataset(path='./dataset', dispose=dispose_value,specific_file=train_files)
        val_dataset = EEG_Dataset(path='./dataset',specific_file=eval_files)
        train_loader = DataLoader(train_dataset, batch_size=train_batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=val_batch_size, shuffle=False)
            
        model = Model(8, 5, PSD_en=True, PLV_en=True).to(device)
        return train(model, train_loader, val_loader, dispose_value,EPOCHS,LR,True,True,tensorboard_en=False)
    
    exps = {}
    exclude_list = [
        [1],
        [2],
        [3],
        [1,2],
        [1,3],
        [2,3]
    ]
    for exclude in exclude_list:
        acc = ds_train(exclude = exclude)
        exps[str(exclude)] = acc
    
    print(exps)

def main_normal():
    EPOCHS = 5
    val_dataset = EEG_Dataset(path='./dataset',symmetry=True)
    train_dataset = EEG_Dataset(path='./dataset', dispose=0,symmetry=True)
    train_loader = DataLoader(train_dataset, batch_size=20, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=500, shuffle=False)
        
    # model = Model(8, 5, PSD_en=True, PLV_en=True).to(device)
    # train(model, train_loader, val_loader, 0,EPOCHS,LR,True,True)
    model = Model(8, 5, PSD_en=False, PLV_en=True).to(device)
    train(model, train_loader, val_loader, 0,EPOCHS,LR,False,True)
    model = Model(8, 5, PSD_en=True, PLV_en=False).to(device)
    train(model, train_loader, val_loader, 0,EPOCHS,LR,True,False)

if __name__ == '__main__':

    main_normal()