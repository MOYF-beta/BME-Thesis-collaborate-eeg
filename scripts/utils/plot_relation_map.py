import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

def plot_relation_map(corr:np.array,chs:list[str]):

    G = nx.Graph()
    n_ch = corr.shape[0] // 2
    assert n_ch * 2 == corr.shape[0]
    assert n_ch * 2 == corr.shape[1]
    assert n_ch == len(chs)
    # 添加两个被试的节点
    for ch in chs:
        G.add_node(f'{ch} 1')
    for ch in reversed(chs):
        G.add_node(f'{ch} 2')

    # 添加边并设置权重
    # 1_1
    edges_1_1 = []
    edges_2_2 = []
    edges_1_2 = []
    for i in range(0,n_ch):
        for j in range(i+1,n_ch):
            edge = (f'{chs[i]} 1', f'{chs[j]} 1')
            G.add_edge(edge[0],edge[1], weight=(corr[i, j]+corr[j, i])/2)
            edges_1_1.append(edge)
            
            edge = (f'{chs[i]} 2', f'{chs[j]} 2')
            G.add_edge(edge[0],edge[1], weight=(corr[i+n_ch, j+n_ch]+corr[j+n_ch, i+n_ch])/2)
            edges_2_2.append(edge)

            edge = (f'{chs[i]} 1', f'{chs[j]} 2')
            G.add_edge(edge[0],edge[1], weight=(corr[i+n_ch, j]+corr[j, i+n_ch])/2)
            edges_1_2.append(edge)

    # 设置位置布局
    pos = nx.circular_layout(G)

    # 绘制图形
    plt.figure(figsize=(12, 12))
    edges = G.edges(data=True)
    weights = [d['weight'] for (u, v, d) in edges]
    max_weight = max(weights)

    # 绘制节点
    nx.draw_networkx_nodes(G, pos, node_size=700, 
                           nodelist=[f'{ch} 1' for ch in chs], node_color='#7FFFD4')
    nx.draw_networkx_nodes(G, pos, node_size=700, 
                           nodelist=[f'{ch} 2' for ch in chs], node_color='#FFB6C1')

    # 绘制标签
    nx.draw_networkx_labels(G, pos, font_size=12, font_color='black')

    # 绘制边，并根据权重设置透明度
    for edge_list, color in [(edges_1_1, '#FFA500'), (edges_2_2, '#228B22'), (edges_1_2, '#DA70D6')]:
        for edge in edge_list:
            # 找到边在 edges 中的位置
            edge_data = next(d for u, v, d in edges if (u, v) == edge or (v, u) == edge)
            alpha = (edge_data['weight'] / max_weight)*0.6 + 0.2  # 计算透明度
            bold = 10 / (1 + np.exp(-7 * (edge_data['weight'] - 0.5)))  # 获取边的粗细
            nx.draw_networkx_edges(G, pos, edgelist=[edge], width=bold, edge_color=color, alpha=alpha)
        
    plt.show()