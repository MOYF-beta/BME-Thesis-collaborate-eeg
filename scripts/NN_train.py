from torch.utils.data import DataLoader
import torch
from torch.optim import Adam
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
from tqdm import tqdm
from eeg_dataset import EEG_Dataset

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
EPOCHS = 200
LR = 0.0001
class Model(nn.Module):
    def __init__(self, n_channel, n_band,n_class = 2):
        super(Model, self).__init__()
        # 图神经网络部分
        self.gcn1 = GCNConv(n_band, n_band * 2)
        self.gcn2 = GCNConv(n_band * 2, 1)
        self.fc_g = nn.Linear(2 * n_channel, 2 * n_channel)
        
        # 二维卷积部分
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 16, kernel_size=3, padding=1)
        self.fc_c = nn.Linear(16 * (2 * n_channel) * (2 * n_channel), 2 * n_channel)
        
        # 后续的全连接层
        self.fc1 = nn.Linear(4 * n_channel, 2 * n_channel)
        self.fc2 = nn.Linear(2 * n_channel, n_channel)
        self.fc3 = nn.Linear(n_channel, n_class)

        self.to(torch.float32)

        self.n_channel = n_channel
        self.busy = False
    
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
        x1 = F.relu(self.gcn1(x1, edge_index))
        x1 = F.dropout(x1, training=self.training)
        x1 = F.relu(self.gcn2(x1, edge_index))
        x1 = x1.view(B, N, -1)  # Reshape back to (B, N, *)
        x1 = x1.view(B, -1)  # Flatten the node features
        x1 = F.relu(self.fc_g(x1))
        
        # 邻接矩阵特征处理
        B, H, W = x2.shape  # B: batch_size, H: height, W: width
        x2 = x2.unsqueeze(1)  # 增加一个通道维度，变成 (B, 1, H, W)
        x2 = F.relu(self.conv1(x2))
        x2 = F.relu(self.conv2(x2))
        x2 = x2.view(B, -1)  # Flatten the convolutional features
        x2 = F.relu(self.fc_c(x2))
        
        # 特征拼接
        x = torch.cat((x2, x1), dim=1)  # Concatenate along the feature dimension
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        x = torch.sigmoid(x)
        return x

def train(model, train_loader, val_loader):
    model.train()  # 设置模型为训练模式
    optimizer = Adam(model.parameters(), lr=LR)
    loss_fn = nn.CrossEntropyLoss()
    scaler = torch.cuda.amp.GradScaler()  # 初始化GradScaler

    progress_epoch = tqdm(range(EPOCHS), desc=f"train progress", position=0)
    for epoch in progress_epoch:
        progress_train = tqdm(train_loader, desc=f"epoch progress", position=1, leave=False)
        
        for batch in progress_train:
            (x_conv, adj_matrix), y = batch
            optimizer.zero_grad()

            with torch.cuda.amp.autocast():  # 启用自动混合精度
                predictions = model(x_conv, adj_matrix)
                loss = loss_fn(predictions, y)
            
            scaler.scale(loss).backward()  # 使用scaler进行反向传播
            scaler.step(optimizer)  # 使用scaler进行优化步骤
            scaler.update()  # 更新scaler

            progress_train.set_postfix(loss=float(loss))
        
        val_loss = evaluate(model, val_loader)
        progress_epoch.set_postfix(loss=float(val_loss))

def evaluate(model, val_loader):
    model.eval()  # 设置模型为评估模式
    loss_fn = nn.CrossEntropyLoss()
    
    with torch.no_grad():  # 在评估过程中不计算梯度
        tot_loss = 0
        for batch in val_loader:
            (x_conv, adj_matrix), y = batch
            with torch.cuda.amp.autocast():  # 启用自动混合精度
                predictions = model(x_conv, adj_matrix)
                tot_loss = tot_loss + loss_fn(predictions, y)
    
    average_loss = tot_loss / len(val_loader)
    return average_loss

def main():
    from tensorboardX import SummaryWriter

    train_dataset = EEG_Dataset(path='./dataset')
    val_dataset = EEG_Dataset(path='./dataset')

    batch_size = 1
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    m = Model(8,5).to(device)
    data = (torch.zeros([1,16,5],dtype=torch.float32).to(device), torch.zeros([1,16,16],dtype=torch.float32).to(device))
    with SummaryWriter("./log", comment="sample_model_visualization") as sw:
        train(m, train_loader, val_loader)
        sw.add_graph(m, data)
        torch.save(m, "./log/m.pt")
    train()


if __name__ == '__main__':
    main()