from functools import lru_cache
import os
from torch.utils.data import DataLoader
import torch
from torch.optim import Adam
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
from tqdm import tqdm
from eeg_dataset import EEG_Dataset
from torch.utils.tensorboard import SummaryWriter
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
EPOCHS = 200
LR = 1e-3
CHECKPOINT_PATH = './log'
os.makedirs(CHECKPOINT_PATH,exist_ok=True)
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

def train(model, train_loader, val_loader):
    global LR
    model.train()  # 设置模型为训练模式
    optimizer = Adam(model.parameters(), lr=LR)
    loss_fn = nn.CrossEntropyLoss()
    scaler = torch.cuda.amp.GradScaler()  # 初始化GradScaler
    
    # 初始化TensorBoard
    writer = SummaryWriter()
    
    best_val_acc = 0.0  # 用于记录最佳模型的验证精度

    progress_epoch = tqdm(range(EPOCHS), desc=f"train progress", position=0)
    for epoch in progress_epoch:
        progress_train = tqdm(train_loader, desc=f"epoch progress", position=1, leave=False)
        for batch in progress_train:
            (x_conv, adj_matrix), y = batch
            optimizer.zero_grad()

            with torch.cuda.amp.autocast():  # 启用自动混合精度
                predictions = model(x_conv, adj_matrix)
                loss = loss_fn(predictions, y)
            if not torch.any(torch.isnan(loss)):
                scaler.scale(loss).backward()  # 使用scaler进行反向传播
                scaler.step(optimizer)  # 使用scaler进行优化步骤
                scaler.update()  # 更新scaler
            else:
                LR = LR * 0.9
            
            progress_train.set_postfix(loss=float(loss))
        
        val_loss, val_acc = evaluate(model, val_loader)
        progress_epoch.set_postfix(loss=float(val_loss), acc=val_acc)
        
        # 记录训练和验证损失及精度到TensorBoard
        writer.add_scalar('Loss/train', loss.item(), epoch)
        writer.add_scalar('Loss/val', val_loss, epoch)
        writer.add_scalar('Accuracy/val', val_acc, epoch)
        
        # 保存最佳模型
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), os.path.join(CHECKPOINT_PATH, 'best_model.pth'))
        
        # 保存当前模型及优化器状态，以便恢复训练
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scaler_state_dict': scaler.state_dict(),
            'best_val_acc': best_val_acc,
            'LR': LR
        }
        torch.save(checkpoint, os.path.join(CHECKPOINT_PATH, 'latest_checkpoint.pth'))
    
    writer.close()  # 关闭TensorBoard

def evaluate(model, val_loader):
    model.eval()  # 设置模型为评估模式
    loss_fn = nn.CrossEntropyLoss()
    correct = 0
    total = 0
    
    with torch.no_grad():  # 在评估过程中不计算梯度
        tot_loss = 0
        for batch in val_loader:
            (x_conv, adj_matrix), y = batch
            y_labels = torch.argmax(y, dim=1)  # 将one-hot向量转换为标签索引
            with torch.cuda.amp.autocast():  # 启用自动混合精度
                predictions = model(x_conv, adj_matrix)
                loss = loss_fn(predictions, y_labels)
                if not torch.any(torch.isnan(loss)):
                    tot_loss = tot_loss + loss
                
                # 计算准确率
                _, predicted = torch.max(predictions.data, 1)
                total += y_labels.size(0)
                correct += (predicted == y_labels).sum().item()
    
    average_loss = tot_loss / len(val_loader)
    accuracy = correct / total
    return average_loss, accuracy

def main():
    from tensorboardX import SummaryWriter

    train_dataset = EEG_Dataset(path='./dataset')
    val_dataset = EEG_Dataset(path='./dataset')

    train_batch_size = 5
    train_loader = DataLoader(train_dataset, batch_size=train_batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=20, shuffle=False)
    m = Model(8,5).to(device)
    train(m,train_loader,val_loader)


if __name__ == '__main__':
    main()