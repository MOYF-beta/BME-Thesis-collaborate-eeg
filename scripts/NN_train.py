import os
import torch
from torch.optim import Adam
import torch.nn as nn
from tqdm import tqdm
from torch.utils.tensorboard import SummaryWriter

def train(model, train_loader, val_loader, dispose_value,EPOCHS,LR,enable_PSD,enable_PLV,CHECKPOINT_PATH = './log'):
    os.makedirs(CHECKPOINT_PATH, exist_ok=True)
    model.train()  # 设置模型为训练模式
    optimizer = Adam(model.parameters(), lr=LR)
    loss_fn = nn.CrossEntropyLoss()
    scaler = torch.cuda.amp.GradScaler()  # 初始化GradScaler
    
    # 初始化TensorBoard
    writer = SummaryWriter(log_dir=os.path.join(CHECKPOINT_PATH, 
                                                f'dispose_{dispose_value}_PSD_{enable_PSD}_PLV_{enable_PLV}'))
    
    best_val_acc = 0.0  # 用于记录最佳模型的验证精度
    hparams = { # 保存一些超参数
        'dispose': dispose_value,
        'enable_PSD': 1 if enable_PSD else 0,
        'enable_PLV': 1 if enable_PLV else 0,
        'lr': LR,
        'epochs': EPOCHS,
        'batch_size': train_loader.batch_size,
        }
    writer.add_hparams(hparams, {})
    
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
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
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
            torch.save(model.state_dict(), os.path.join(CHECKPOINT_PATH, f'best_model_dispose_{dispose_value}.pth'))
        
        # 保存当前模型及优化器状态，以便恢复训练
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scaler_state_dict': scaler.state_dict(),
            'best_val_acc': best_val_acc,
            'LR': LR
        }
        torch.save(checkpoint, os.path.join(CHECKPOINT_PATH, f'latest_checkpoint_dispose_{dispose_value}.pth'))
    
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

