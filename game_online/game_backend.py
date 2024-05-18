from psychopy import core, event
from game_frontend import Trtris_map
class game_backend:

    def __init__(self) -> None:
        # TODO psychopy core、game、对方服务器地址、AB组别、twisted
        self.game : Trtris_map = None
        self.game_mode = 'single' # single/multi
        self.multi_player_seed = 0
        self.group = None # A/B
        self.task = None # slide/rotate

        self.game_running = False
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

    def handle_server_msg(msg:dict):
        if not msg.__contains__('op'):
            return
        if msg['op'] == 'start_single':
            
            pass
        elif msg['op'] == 'end_single':
            # 设置 Trtris_map 的game_over flag
            pass
        elif msg['op'] == 'start_multi':
            pass
        elif msg['op'] == 'sync_beat':
            pass
        elif msg['op'] == 'end_multi':
            pass
        # 处理 start_single
        # 处理 end_single
        # 处理 start_multi
        # 处理 sync_beat
        # 处理 end_multi
        pass

    def main_thread(self):
        # 检查flag，每新开一局创建一个新的 Trtris_map
        pass