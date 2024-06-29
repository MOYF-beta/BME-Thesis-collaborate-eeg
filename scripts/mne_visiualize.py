import matplotlib.pyplot as plt
import numpy as np

# 定义电极位置
electrode_positions = {
    'C3': [0, 0],
    'F7': [-0.5, 1],
    'P4': [0.5, -1],
    'Oz': [0, -1.5],
    'F2': [0.5, 1],
    'O1': [-0.5, -1.5],
    'T7': [-1, 0],
    'T8': [1, 0]
}

# 定义连接关系和强度数据
connections_single = [
    ('C3', 'F7', 0.55, 0.20, 0.16, 0.48),
    ('P4', 'Oz', 1.00, 0.48, 0.49, 0.33),
    ('F2', 'O1', 0.98, 0.31, 1.00, 0.61),
    ('C3', 'O1', 0.78, 0.05, 0.44, 0.56),
    ('P4', 'O1', 0.59, 0.19, 0.41, 0.32),
    ('C3', 'F2', 0.77, 0.16, 0.79, 0.41),
    ('T7', 'C3', 0.86, 0.04, 0.85, 0.41),
    ('P4', 'C3', 0.57, 0.08, 0.15, 0.30),
    ('T7', 'P4', 0.57, 0.50, 0.28, 0.49),
    ('T8', 'P4', 0.65, 0.13, 0.28, 0.30),
    ('F2', 'C3', 0.55, 0.22, 0.22, 0.31),
    ('T7', 'C3', 0.53, 0.16, 0.75, 0.27),
    ('Oz', 'P4', 0.63, 0.42, 0.40, 0.36),
    ('T8', 'C3', 0.00, 0.00, 0.57, 0.48),
    ('P4', 'T7', 0.00, 0.00, 0.70, 0.65)
]

connections_cross = [
    ('O1', 'T7', 0.59, 0.02, 0.16, 0.08),
    ('C3', 'T7', 0.74, 0.05, 0.17, 0.09),
    ('T8', 'Oz', 0.00, 0.00, 0.52, 0.15),
    ('Oz', 'P4', 0.00, 0.00, 0.50, 0.07)
]

def plot_connections(ax, connections, condition):
    for (elec1, elec2, signif_coop, strength_coop, signif_comp, strength_comp) in connections:
        pos1 = electrode_positions[elec1]
        pos2 = electrode_positions[elec2]
        if condition == 'cooperation':
            color = 'blue' if '↑' in str(strength_coop) else 'red'
            lw = signif_coop * 5  # 根据显著值调整线条粗细
        elif condition == 'competition':
            color = 'red' if '↑' in str(strength_comp) else 'blue'
            lw = signif_comp * 5  # 根据显著值调整线条粗细
        ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], color=color, lw=lw)

def plot_head_outline(ax):
    circle = plt.Circle((0, 0), 1.5, color='black', fill=False, lw=2)
    ax.add_artist(circle)
    ears = np.array([[-1.5, 0.5], [-1.7, 0.5], [-1.7, -0.5], [-1.5, -0.5], 
                     [1.5, 0.5], [1.7, 0.5], [1.7, -0.5], [1.5, -0.5]])
    ax.plot(ears[:4, 0], ears[:4, 1], color='black', lw=2)
    ax.plot(ears[4:, 0], ears[4:, 1], color='black', lw=2)

# 绘制单脑合作图
fig, ax = plt.subplots()
for name, pos in electrode_positions.items():
    ax.scatter(pos[0], pos[1], s=100, c='black')
    ax.text(pos[0], pos[1], name, fontsize=12, ha='center')
plot_connections(ax, connections_single, 'cooperation')
plot_head_outline(ax)
ax.set_title('Single Brain Cooperation')
plt.axis('off')

# 绘制单脑对抗图
fig, ax = plt.subplots()
for name, pos in electrode_positions.items():
    ax.scatter(pos[0], pos[1], s=100, c='black')
    ax.text(pos[0], pos[1], name, fontsize=12, ha='center')
plot_connections(ax, connections_single, 'competition')
plot_head_outline(ax)
ax.set_title('Single Brain Competition')
plt.axis('off')

# 绘制跨脑合作图
fig, ax = plt.subplots()
for name, pos in electrode_positions.items():
    ax.scatter(pos[0], pos[1], s=100, c='black')
    ax.text(pos[0], pos[1], name, fontsize=12, ha='center')
plot_connections(ax, connections_cross, 'cooperation')
plot_head_outline(ax)
ax.set_title('Cross Brain Cooperation')
plt.axis('off')

# 绘制跨脑对抗图
fig, ax = plt.subplots()
for name, pos in electrode_positions.items():
    ax.scatter(pos[0], pos[1], s=100, c='black')
    ax.text(pos[0], pos[1], name, fontsize=12, ha='center')
plot_connections(ax, connections_cross, 'competition')
plot_head_outline(ax)
ax.set_title('Cross Brain Competition')
plt.axis('off')

plt.show()
