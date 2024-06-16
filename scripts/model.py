import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
from functools import lru_cache
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class Model(nn.Module):
    def __init__(self, n_channel, n_band,n_class = 2):
        super(Model, self).__init__()
        # 图神经网络部分
        self.gcn1 = GCNConv(n_band, n_band * 8)
        self.gcn2 = GCNConv(n_band * 8, n_band * 8)
        self.gcn3 = GCNConv(n_band * 8, n_band * 8)
        self.gcn4 = GCNConv(n_band * 8, 1)
        self.fc_g = nn.Linear(2 * n_channel, 2 * n_channel)
        
        # 二维卷积部分
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 16, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(16, 16, kernel_size=3, padding=1)
        self.conv4 = nn.Conv2d(16, 16, kernel_size=3, padding=1)
        self.fc_c = nn.Linear(16 * (2 * n_channel) * (2 * n_channel), 2 * n_channel)
        
        # 后续的全连接层
        self.fc1 = nn.Linear(4 * n_channel, 2 * n_channel)
        self.fc2 = nn.Linear(2 * n_channel, n_channel)
        self.fc3 = nn.Linear(n_channel, n_class)

        self.to(torch.float32)

        self.n_channel = n_channel
    
    @lru_cache
    def create_fully_connected_edge_index(self):
        # 创建一个全连接图
        rows, cols = torch.meshgrid(torch.arange(2 * self.n_channel), torch.arange(2 * self.n_channel), indexing='ij')
        mask = rows != cols
        return torch.stack([rows[mask], cols[mask]], dim=0).to(device)

    def forward(self, x1, x2):
    # 图特征处理
        edge_index = self.create_fully_connected_edge_index()
        
        B, N, Features = x1.shape  # B: batch_size, N: num_nodes, F: num_features_per_node
        x1 = x1.view(B * N, Features)  # Reshape for GCN input
        x1 = self.gcn1(x1, edge_index)
        x1 = self.gcn2(x1, edge_index)
        x1 = self.gcn3(x1, edge_index)
        x1 = self.gcn4(x1, edge_index)
        
        x1 = x1.view(B, N, -1)  # Reshape back to (B, N, *)
        x1 = x1.view(B, -1)  # Flatten the node features
        x1 = self.fc_g(x1)
        
        # 邻接矩阵特征处理
        B, H, W = x2.shape  # B: batch_size, H: height, W: width
        x2 = x2.unsqueeze(1)  # 增加一个通道维度，变成 (B, 1, H, W)
        x2 = self.conv1(x2)
        x2 = self.conv2(x2)
        x2 = self.conv3(x2)
        x2 = self.conv4(x2)
        x2 = x2.view(B, -1)  # Flatten the convolutional features
        x2 = F.leaky_relu(self.fc_c(x2))
        
        # 特征拼接
        x = torch.cat((x2, x1), dim=1)  # Concatenate along the feature dimension
        x = F.leaky_relu(self.fc1(x))
        x = F.dropout(x, training=self.training,p = 0.3)
        x = self.fc2(x)
        x = self.fc3(x)
        x = torch.sigmoid(x)
        return x