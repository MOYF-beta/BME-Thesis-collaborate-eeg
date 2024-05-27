import time
import socket
from typing import Callable
from psychopy import core,event
from twisted_network_protocol import twisted_game_networking

class game_backend:

    slide_direction = 0
    rotate_direction = 0
    space_pressed = False

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

    def get_key_status(self):

        game_backend.slide_direction = 0
        game_backend.rotate_direction = 0
        game_backend.space_pressed = False
        keys_pressed = event.getKeys()
        if self.game_mode == 'single' or self.task == 'slide':
            if 'z' in keys_pressed:
                game_backend.slide_direction -= 1
            if 'x' in keys_pressed:
                game_backend.slide_direction += 1
        if self.game_mode == 'single' or self.task == 'rotate':
            if 'comma' in keys_pressed: # <
                game_backend.rotate_direction += 1
            if 'period' in keys_pressed: # >
                game_backend.rotate_direction -= 1
        if 'space' in keys_pressed: 
            game_backend.space_pressed = True
        if(len(keys_pressed)>0):
            print(keys_pressed)

        if self.game_mode == 'multi':
            # 多人模式，属于自己job的按键事件驱动游戏并发送给同伙
            self.send_remote_key()
        else:
            self.callbacks['block_slide'](game_backend.slide_direction)
            self.callbacks['block_rotate'](game_backend.rotate_direction)
            if game_backend.space_pressed:
                self.callbacks['space_pressed']()
        
            
    def send_remote_key(self):
        data = {'k':[]}
        need_send = False
        if self.task == 'slide' and game_backend.slide_direction != 0:
            data['k'].append(1 if game_backend.slide_direction >0 else 2) 
            need_send = True
        elif self.task == 'rotate' and game_backend.rotate_direction != 0:
            data['k'].append(3 if game_backend.slide_direction >0 else 4) 
            need_send = True
        if game_backend.space_pressed:
            data['k'].append(5)
            need_send = True
        if need_send:
            self.net_layer.send_key(data)

    def handle_game_data(self,data:dict):
        keys = data.keys()
        if 's' in keys:
            # 收到来自服务器的更新节拍，给游戏更新flag打true
            if self.game_running and self.game_mode == 'multi':
                self.callbacks['update_multiplayer_flag']()
            return
        if 'k' not in keys:
            print(f"warning:unknow pack recived{data}")
            return
        key_event = data['k']
        if 1 in key_event:
            game_backend.slide_direction = 1
        if 2 in key_event:
            game_backend.slide_direction = -1
        if 3 in key_event:
            game_backend.rotate_direction = 1
        if 4 in key_event:
            game_backend.rotate_direction = -1
        if 5 in key_event:
            game_backend.space_pressed = True
        
        self.callbacks['block_slide'](game_backend.slide_direction)
        self.callbacks['block_rotate'](game_backend.rotate_direction)
        if game_backend.space_pressed:
            self.callbacks['space_pressed']()
        

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
            self.game_running = True
            self.callbacks['start_game'](True)

        elif op == 'es' or op == 'em': # end_single,end_multi
            self.game_running = False
            self.game_mode = None
            self.callbacks['end_game']()
