import time
import socket
from typing import Callable
from psychopy import core,event
from twisted_network_protocol import game_net

class game_backend:

    slide_direction = 0
    rotate_direction = 0
    space_pressed = False

    def get_all_ip_addresses():
        ip_list = []
        hostname = socket.gethostname()
        ip_addresses = socket.getaddrinfo(hostname, None)
        
        for addr in ip_addresses:
            ip = addr[4][0]
            if ip not in ip_list:
                ip_list.append(ip)
        
        return ip_list

    def __init__(self,callbacks:dict[str,Callable]) -> None:

        self.callbacks = callbacks

        self.game_mode = None # single/multi
        self.multi_player_seed = 0
        self.group = None # A/B
        self.task = None # slide/rotate

        self.game_running = False
        self.ip_list = game_backend.get_all_ip_addresses() #获得本机的所有ip地址
        self.other_player_ip = None

        self.net_transport = game_net(self.handle_server_msg,self.handle_remote_key)
    
    def run(self):
        self.net_transport.run_ctrl_transport()
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
        self.callbacks['block_slide'](game_backend.slide_direction)
        self.callbacks['block_rotate'](game_backend.rotate_direction)
        if game_backend.space_pressed:
            self.callbacks['space_pressed']()
            
    def send_remote_key(self):
        data = {}
        need_send = False
        if self.task == 'slide' and game_backend.slide_direction != 0:
            data['s'] = game_backend.slide_direction
            need_send = True
        elif self.task == 'rotate' and game_backend.rotate_direction != 0:
            data['r'] = game_backend.rotate_direction
            need_send = True
        if game_backend.space_pressed:
            data['!'] = 1
            need_send = True
        if need_send:
            self.net_transport.send_key(data)

    def handle_remote_key(data:dict):
        if 's' in data.keys:
            game_backend.slide_direction = data['s']
        if 'r' in data.keys:
            game_backend.rotate_direction = data['r']
        if '!' in data.keys and data['!'] == 1:
            game_backend.space_pressed = True
        

    def handle_server_msg(self,msg:dict):
        if 'op' not in msg:
            return
        op = msg['op']
        
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
            self.other_player_ip = (set(msg['ip']) - set(self.ip_list)).pop()

            self.net_transport.run_key_event_transport(self.task,self.other_player_ip)

            if 'seed' in msg:
                self.multi_player_seed = msg['seed']
            self.game_running = True
            self.callbacks['start_game'](True)

        elif op == 'sb': # sync_beat
            # 收到来自服务器的更新节拍，给游戏更新flag打true
            if self.game_running and self.game_mode == 'multi':
                self.callbacks['update_multiplayer_flag']()

        elif op == 'es' or op == 'em': # end_single,end_multi
            self.game_running = False
            self.game_mode = None
            self.callbacks['end_game']()
