import time
import socket
from psychopy import event
from game_frontend import Trtris_map
from twisted_network_protocol import game_net
import threading



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

    def __init__(self) -> None:
        self.game : Trtris_map = None
        self.game_mode = 'single' # single/multi
        self.multi_player_seed = 0
        self.group = None # A/B
        self.task = None # slide/rotate

        self.game_running = False
        self.ip_list = game_backend.get_all_ip_addresses() #获得本机的所有ip地址
        self.other_player_ip = None

        self.net_transport = game_net()

    def key_listen_thread(self):
        while self.game_running:
            game_backend.slide_direction = 0
            game_backend.rotate_direction = 0
            game_backend.space_pressed = False
            keys_pressed = event.getKeys()
            if 'z' in keys_pressed:
                game_backend.slide_direction -= 1
            if 'x' in keys_pressed:
                game_backend.slide_direction += 1
            if 'comma' in keys_pressed: # <
                game_backend.rotate_direction += 1
            if 'period' in keys_pressed: # >
                game_backend.rotate_direction -= 1
            if 'space' in keys_pressed: 
                game_backend.space_pressed = True

            if self.game_mode == 'single':
                # 单人模式下按键时间直接驱动游戏
                self.game.block_slide(game_backend.slide_direction)
                self.game.block_rotate(game_backend.rotate_direction)
                self.game.space_pressed = game_backend.space_pressed

            elif self.game_mode == 'multi':
                # 多人模式，属于自己job的按键事件驱动游戏并发送给同伙
                if self.task == 'slide' and game_backend.slide_direction != 0:
                    self.send_remote_key(game_backend.slide_direction)
                    self.game.block_slide(game_backend.slide_direction)
                elif self.task == 'rotate' and game_backend.rotate_direction != 0:
                    self.send_remote_key(game_backend.rotate_direction)
                    self.game.block_rotate(game_backend.rotate_direction)
                if game_backend.space_pressed:
                    # 两人都有权使用空格
                    self.send_remote_key(game_backend.space_pressed)
                self.game.space_pressed = game_backend.space_pressed
            
    def send_remote_key(self):
        data = {}
        if self.task == 'slide':
            data['s'] = game_backend.slide_direction
        elif self.task == 'rotate':
            data['r'] = game_backend.rotate_direction
        if game_backend.space_pressed:
            data['!'] = 1
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
            self.net_transport.resopnd_beat_server(msg['group'])
        if op == 'at': # arrange_group
            assert 'task' in msg
            self.task = msg['task']
            self.net_transport.resopnd_beat_server(msg['task'])
        elif op == 'ss': # start_single
            assert not self.game_running
            assert self.group is not None
            self.game_running = True
            threading.Thread(target=self.single_mode_thread,args=[self.group])
            
        elif op == 'sm': # start_multi
            assert not self.game_running
            assert self.group is not None 
            # 提取信息
            assert 'ip' in msg
            self.other_player_ip = (msg['ip'] - self.ip_list).pop()
            if 'seed' in msg:
                self.multi_player_seed = msg['seed']
            threading.Thread(target=self.multi_mode_thread,args=[self.group])
            self.game_running = True
            pass

        elif op == 'sb': # sync_beat
            # 收到来自服务器的更新节拍，给游戏更新flag打true
            assert self.game_running
            assert self.game_mode == 'multi'
            self.game.multiplayer_update_flag = True

        elif op == 'es' or op == 'em': # end_single,end_multi
            if self.game is not None:
                self.game.game_over = True
            self.game_running = False

    def single_mode_thread(self,group:str):
        while self.game_running:
            self.game = Trtris_map(False,group)
            while not self.game.game_over:
                time.sleep(1)
            self.game = None
    
    def multi_mode_thread(self,group:str):
        self.game = Trtris_map(True,group)
        self.net_transport.run_key_event_transport(self.task,self.other_player_ip)
        while not self.game.game_over:
            time.sleep(1)
        self.game = None
        
    
