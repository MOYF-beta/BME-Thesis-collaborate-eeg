import time
from typing import Callable
import numpy as np
from psychopy import event
from twisted_network_protocol import twisted_game_networking

class game_backend:

    def __init__(self,callbacks:dict[str,Callable]) -> None:

        self.callbacks = callbacks

        self.game_mode = None # single/multi
        self.multi_player_seed = 0
        self.group = None # A/B
        self.task = None # slide/rotate

        self.game_running = False
        self.net_layer = twisted_game_networking(self.handle_data)
    
    def run(self):
        self.net_layer.run_ctrl_transport()
        while True:
            time.sleep(1)

    def handle_game_data(self,data:dict):
        keys = data.keys()
        if 's' in keys: # S : Sync beat
            # 收到来自服务器的更新节拍，给游戏更新flag打true
            if self.game_running and self.game_mode == 'multi':
                self.callbacks['update_multiplayer_flag']()
            return
        
        if 'f' in keys:
            # 现在的思路下只是用来显示按下空格的
            self.callbacks['space_pressed']()
            return

        if 'b' in keys: # falling Block
            block_coord = data['b']
            block_coord_np = []
            for i in range(len(block_coord)/2):
                block_coord_np.append(np.array([block_coord[i*2],block_coord[i*2+1]]))
            self.callbacks['set_falling_blocks'](block_coord_np)
            return

        print(f"warning:unknow pack recived{data}")
        return
        
    def send_falling_blocks(self,blocks_np):
        blocks_list = []
        for coord in blocks_np:
            blocks_list.append(int(coord[0]))
            blocks_list.append(int(coord[1]))

        self.net_layer.send_data_to_server({'b':blocks_list})

    def send_event_space_pressed(self):
        self.net_layer.send_data_to_server({'f':1})

    
    def handle_data(self,msg:dict):
        if 'op' not in msg.keys():
            # 没有op字段的视作游戏数据
            self.handle_game_data(msg)
            return
        # 处理控制信息
        op = msg['op']
        print(f"{msg}")
        if op == 'ag': # arrange_group
            assert 'group' in msg
            self.group = msg['group']
            self.callbacks['set_group'](msg['group'])
            # self.net_transport.resopnd_beat_server(msg['group'])
        elif op == 'at': # arrange_group
            assert 'task' in msg
            self.task = msg['task']
            # self.net_transport.resopnd_beat_server(msg['task'])
        elif op == 'ss': # start_single
            assert not self.game_running
            assert self.group is not None
            self.game_running = True
            self.game_mode = 'single'
            self.callbacks['start_game'](False)
            
        elif op == 'sm': # start_multi
            assert self.group is not None 
            # 提取信息
            assert 'ip' in msg
            self.game_mode = 'multi'

            if 'seed' in msg:
                self.multi_player_seed = msg['seed']
                self.callbacks['set_seed'](self.multi_player_seed)
            self.game_running = True
            self.callbacks['start_game'](True)

        elif op == 'es' or op == 'em': # end_single,end_multi
            self.game_running = False
            self.game_mode = None
            self.callbacks['end_game']()
