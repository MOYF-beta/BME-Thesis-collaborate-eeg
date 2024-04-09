import torch
from torch.optim import Adam
import numpy as np
from threading import Semaphore
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv

class Model(nn.Module):
    def __init__(self, n_channel, n_band):
        super(Model, self).__init__()
        # 一维卷积层
        self.conv1 = nn.Conv1d(in_channels=2*n_channel, out_channels=2*n_channel, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv1d(in_channels=2*n_channel, out_channels=2*n_channel, kernel_size=n_band - 1, stride=n_band - 1)  # 假设通过这一层减少到1
        
        # 图神经网络层
        self.gcn1 = GCNConv(2*n_channel, 2*n_channel)
        self.gcn2 = GCNConv(2*n_channel, 1)  # 假设第二层GCN输出1个特征
        
        # 全连接层
        self.fc1 = nn.Linear(2*n_channel + 2*n_channel, 2*n_channel)  # 假设拼接后的特征大小
        self.fc2 = nn.Linear(2*n_channel, 1)
        
    def forward(self, x_conv, adj_matrix):
        # 处理第一个特征
        x_conv = x_conv.permute(0, 2, 1)  # 为了匹配Conv1d的输入维度需求
        x_conv = F.relu(self.conv1(x_conv))
        x_conv = F.relu(self.conv2(x_conv))
        x_conv = x_conv.view(x_conv.size(0), -1)  # 扁平化
        
        # 处理图特征
        x_gcn = F.relu(self.gcn1(adj_matrix, adj_matrix))
        x_gcn = F.relu(self.gcn2(x_gcn, adj_matrix))
        x_gcn = x_gcn.view(x_gcn.size(0), -1)  # 扁平化
        
        # 拼接两个特征
        x = torch.cat((x_conv, x_gcn), dim=1)
        
        # 全连接层
        x = F.relu(self.fc1(x))
        x = torch.sigmoid(self.fc2(x))  # 假设最终输出是归一化的
        
        return x

class RegressionOpti:
    def __init__(self, n_channel, n_band, n_thread=4):
        self.n_channel = n_channel
        self.n_band = n_band
        self.model_pool = [Model(n_channel, n_band) for _ in range(n_thread + 1)]
        self.semaphore = Semaphore(n_thread + 1)  # 控制对模型池的访问


    def _train(self, model, train_data, val_loader):
        model.train()  # 设置模型为训练模式
        optimizer = Adam(model.parameters())
        loss_fn = nn.MSELoss()
        
        patience = 10  # 早停耐心值
        patience_counter = 0  # 耐心计数器
        best_val_loss = float('inf')
        
        while patience_counter < patience:
            for x_conv, adj_matrix, y in train_data:
                optimizer.zero_grad()
                # 假设model.forward能够处理对应的输入
                predictions = model(x_conv, adj_matrix)
                loss = loss_fn(predictions, y)
                loss.backward()
                optimizer.step()
            
            val_loss = self._evaluate(model, val_loader)
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0  # 重置耐心计数器
            else:
                patience_counter += 1  # 未改善则增加耐心计数器
    def _evaluate(self, model, val_data):
        model.eval()  # 设置模型为评估模式
        loss_fn = nn.MSELoss()
        
        total_loss = 0.0
        total_samples = 0
        
        with torch.no_grad():  # 在评估过程中不计算梯度
            x_conv, adj_matrix, y = val_data
            predictions = model(x_conv, adj_matrix)
            loss = loss_fn(predictions, y)
            total_loss += loss.item() * y.size(0)
            total_samples += y.size(0)
        
        average_loss = total_loss / total_samples
        return average_loss


    def train_eval(self, data):
        # 等待获取一个模型
        self.semaphore.acquire()
        model = self._get_idle_model()
        if model is None:
            raise Exception("No idle model available.")
        
        # 这里是训练和验证的伪代码，需要实现实际的训练逻辑
        all_losses = []
        for i, (x_conv, adj_matrix, y) in enumerate(data):

            self._train(model, data[:i] + data[i+1:]) # 除了编号为i的其余元素
            loss = self._evaluate(model,(x_conv, adj_matrix, y))
            all_losses.append(loss)
        
        # 重置模型和优化器，然后标记模型为闲置
        self._reset_model(model)
        self.semaphore.release()

        # 返回所有验证集的loss均值
        return np.mean(all_losses)

    def _get_idle_model(self):
        # 返回一个空闲的模型，实际实现中需要确保线程安全
        for model in self.model_pool:
            if not model.busy:
                model.busy = True
                return model
        return None

    def _reset_model(self, model):
        # 重置模型和优化器到初始状态
        model.__init__(self.n_channel, self.n_band)  # 重置模型参数
        model.busy = False  # 标记模型为闲置

