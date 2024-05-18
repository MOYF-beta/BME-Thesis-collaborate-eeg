from psychopy import core, event
from game_frontend import Trtris_map
from twisted import 
import threading



class game_backend:

    def __init__(self) -> None:
        # TODO psychopy core、game、对方服务器地址、AB组别、twisted
        self.game : Trtris_map = None
        self.game_mode = 'single' # single/multi
        self.multi_player_seed = 0
        self.group = None # A/B
        self.task = None # slide/rotate

        self.game_running = False
        self.ip = None # TODO 需要初始化ip
        self.other_player_ip = None

        self.slide_direction = 0
        self.rotate_direction = 0
        self.space_pressed = False

    def key_listen_thread(self):
        while self.game_running:
            self.slide_direction = 0
            self.rotate_direction = 0
            keys_pressed = event.getKeys()
            if 'z' in keys_pressed:
                self.slide_direction -= 1
            if 'x' in keys_pressed:
                self.slide_direction += 1
            if 'comma' in keys_pressed: # <
                self.rotate_direction += 1
            if 'period' in keys_pressed: # >
                self.rotate_direction -= 1
            if 'space' in keys_pressed: 
                self.space_pressed = True

            if self.game_mode == 'single':
                # 单人模式下按键时间直接驱动游戏
                self.game.block_slide(self.slide_direction)
                self.game.block_rotate(self.rotate_direction)
                self.game.space_pressed = self.space_pressed
            elif self.game_mode == 'multi':
                # 多人模式，属于自己job的按键事件驱动游戏并发送给同伙
                if self.task == 'slide' and self.slide_direction != 0:
                    self.game.block_slide(self.slide_direction)
                    self.send_remote_key(self.slide_direction)
                elif self.task == 'rotate' and self.rotate_direction != 0:
                    self.send_remote_key(self.rotate_direction)
                    self.game.block_rotate(self.rotate_direction)
                if self.space_pressed:
                    # 两人都有权使用空格
                    self.send_remote_key(self.rotate_direction)
                    self.game.space_pressed = self.space_pressed
            
    def send_remote_key(self):
        # TODO twisted 发送
        # 设置game的操作值
        pass
    def handle_remote_key():
        # twisted 信息回调函数，设置game的操作值
        # self.slide_direction、self.rotate_direction
        pass

    def handle_server_msg(self,msg:dict):
        if 'op' not in msg:
            return
        op = msg['op']

        # if op == 'contact_me': # 服务器用于发现客户端，客户端向来源地址发送udp包
        #     pass #TODO 回复服务器 ack

        if op == 'tell_ip':
            assert 'ip' in msg
            self.ip = msg['ip']
        
        elif op == 'arrange_group':
            assert 'group' in msg
            self.group = msg['group']
            # TODO 回复服务器 ack

        elif op == 'start_single':
            assert not self.game_running
            assert self.group is not None
            self.game_running = True
            threading.Thread(target=self.single_mode_thread,args=[self.group])
            
        elif op == 'start_multi':
            assert not self.game_running
            assert self.group is not None 
            # 提取信息
            assert 'task' in msg
            assert 'ip' in msg
            self.task = msg['task']
            self.other_player_ip = (msg['ip'] - {self.ip}).pop()
            if 'seed' in msg:
                self.multi_player_seed = msg['seed']

            threading.Thread(target=self.multi_mode_thread,args=[self.group])
            self.game_running = True
            pass

        elif op == 'sync_beat':
            # 收到来自服务器的更新节拍，给游戏更新flag打true
            assert self.game_running
            assert self.game_mode == 'multi'
            self.game.multiplayer_update_flag = True

        elif op == 'end_single' or op == 'end_multi':
            if self.game is not None:
                self.game.game_over = True
            self.game_running = False

    def single_mode_thread(self,group:str):
        while self.game_running:
            self.game = Trtris_map(False,group)
            while not self.game.game_over:
                pass
            self.game = None
    
    def multi_mode_thread(self,group:str):
        self.game = Trtris_map(True,group)
        # TODO 创建 twisted 实例
        while not self.game.game_over:
            pass
        self.game = None
        
    
