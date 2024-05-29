from psychopy import visual, core
from game_backend import game_backend
from tetris_shape import tetris_shapes,tetris_color
import numpy as np
import threading
from net_config import step_time,read_tip_time
from game_strategy import group_A,group_B

# TODO 1、改变UI，显示按键状态
# TODO 2、添加全屏提示


class Trtris_map:

    def callback_set_gamemode(self,is_multiplayer:bool):
        self.is_multiplayer = is_multiplayer
    
    def callback_set_seed(self,seed:int):
        self.seed = seed
    
    def callback_set_group(self,group:str):
        assert group == 'A' or group == 'B'
        self.group = group
        if group == 'A':
            self.game_strategy = group_A()
        else:
            self.game_strategy = group_B()
    
    def callback_space_pressed(self):
        self.space_pressed = True
        self.key_space.draw()
        self.game_strategy.space_bouns()
    
    def game_grapic_init(self):
        # convoluted shit
        self.game_step_count = 0
        self.mat_logic = np.zeros(self.map_size,dtype=np.int8)
        self.mat_color = np.zeros(self.map_size,dtype=np.int8)
        self.game_score = 0
        self.game_over = False
        self.pack_no = 0
        self.pack = np.array(range(7),dtype=np.int8)
        self.slide_direction = 0
        self.rotate_direction = 0
        self.space_pressed = False
        self.game_score_text.text = f'Score: {self.game_score}'
    
    def backend_ctrl_param_init(self): 
        self.slide_direction = 0
        self.rotate_direction = 0
        self.space_pressed = False
    
    def start_game(self,is_multiplayer:bool):
        self.is_multiplayer = is_multiplayer
        self.game_running = True
    
    def end_game(self):
        self.game_running = False
        self.game_over = True
    
    def callback_update_multiplayer_flag(self):
        self.game_update_flag = True
    
    def callback_block_slide(self,slide_direction):
        self.slide_direction = slide_direction
        if self.slide_direction == 1:
            self.key_x.draw()
        elif self.slide_direction == -1:
            self.key_z.draw()
    
    def callback_block_rotate(self,rotate_direction):
        self.rotate_direction = rotate_direction
        if self.rotate_direction == -1:
            self.key_rr.draw()
        elif self.rotate_direction == 1:
            self.key_rl.draw()
    
    def callback_multiplayer_standby(self,p1:bool,p2:bool):
        pass # TODO 根据需求2呈现玩家准备的状态

    def _get_positions_gameplay(self, map_size, rect_size, margin):
        positions = []
        for i in range(map_size[0]):
            for j in range(map_size[1]):
                x = margin + -1 + i * rect_size + 0.5 * rect_size
                y = -1 + j * rect_size + 0.5 * rect_size
                positions.append((x, y))
        return positions

    def _get_positions_preview(self, rect_size):
        positions = []
        for i in range(3):
            for j in range(4):
                x = 0.6 - rect_size * 3 + i * rect_size + 1.6 * rect_size
                y = 0.6 - rect_size * 4 + j * rect_size + 0.5 * rect_size
                positions.append((x, y))
        return positions

    def __init__(self, map_size = (10,20),win_shape = (800,800),
                 game_zone_width = 0.7, margin = 0.1) -> None:
        self.win = visual.Window(size=win_shape, winType='pyglet')
        self.map_size = map_size
        rect_size = (game_zone_width - 2 * margin)/map_size[0] * 2 
        nElements = map_size[0] * map_size[1]
        self.gameplay_area = visual.ElementArrayStim(win=self.win, 
                                          nElements=nElements, 
                                          elementTex=None, 
                                          elementMask="rect", 
                                          sizes=rect_size, 
                                          xys=self._get_positions_gameplay(map_size, rect_size, margin), 
                                          colors=[0,0,0])
        self.preview_area = visual.ElementArrayStim(win=self.win, 
                                          nElements=4*3, 
                                          elementTex=None, 
                                          elementMask="rect", 
                                          sizes=rect_size, 
                                          xys=self._get_positions_preview(rect_size), 
                                          colors=[0,0,0])
        
        self.next_block_text = visual.TextStim(win=self.win, text='Next:', pos=(0.6, 0.6 + rect_size), color=(1, 1, 1))
        self.game_score_text = visual.TextStim(win=self.win, text='Score: 0', pos=(0.6, 0.2-rect_size), color=(1, 1, 1))

        self.key_z = visual.TextStim(win=self.win, text='Z', pos=(0.4, 0.1-rect_size), color=(1, 0, 0),bold=True)
        self.key_x = visual.TextStim(win=self.win, text='X', pos=(0.5, 0.1-rect_size), color=(1, 0, 0),bold=True)
        self.key_rl = visual.TextStim(win=self.win, text='<', pos=(0.6, 0.1-rect_size), color=(1, 0, 0),bold=True)
        self.key_rr = visual.TextStim(win=self.win, text='>', pos=(0.7, 0.1-rect_size), color=(1, 0, 0),bold=True)
        self.key_space = visual.TextStim(win=self.win, text='Space', pos=(0.7, 0.1-rect_size*2), color=(1, 0, 0),bold=True)

        self.seed = None
        self.group = None # A/B
        self.is_multiplayer = None
        self.game_update_flag = False # 在多人模式，服务器发送beat信号设置此flag，让游戏进行一次更新
        self.game_running = False
        self.callbacks = {
            'set_gamemode':self.callback_set_gamemode,
            'set_group':self.callback_set_group,
            'set_seed':self.callback_set_seed,
            'space_pressed':self.callback_space_pressed,
            'block_slide':self.callback_block_slide,
            'block_rotate':self.callback_block_rotate,
            'start_game':self.start_game,
            'end_game':self.end_game,
            'update_multiplayer_flag':self.callback_update_multiplayer_flag,
            'multiplayer_standby':self.callback_multiplayer_standby
        }
        self.game_grapic_init()
        self.backend_ctrl_param_init()
        self.backend = game_backend(self.callbacks)
        self.game_strategy = None

    def graphic_step(self): 
        map_colors = [tetris_color[self.mat_color[i, j]] 
                  for i in range(self.map_size[0]) 
                  for j in range(self.map_size[1])]
        self.gameplay_area.colors = map_colors
        [w,h] = tetris_shapes[self.next_block_no].shape
        preview_colors = [tetris_color[self.next_block_no+1] if i<w and j<h and tetris_shapes[self.next_block_no][i,j] != 0 else tetris_color[0]
                  for i in range(3) 
                  for j in range(4)]
        self.preview_area.colors = preview_colors

        self.game_score_text.text = f'得分: {self.game_strategy.score}'

        self.gameplay_area.draw()
        self.preview_area.draw()
        self.next_block_text.draw()
        self.game_score_text.draw()
        self.win.flip()


    def game_step(self):

        def block_spawn(shape_no):
            new_blocks_mask = tetris_shapes[shape_no]
            new_blocks_color = shape_no + 1
            [new_width,new_height] = new_blocks_mask.shape
            spawn_x = self.map_size[0] // 2 - new_width // 2
            if not np.any(np.logical_and(new_blocks_mask != 0,
                                          self.mat_logic[spawn_x:spawn_x + new_width,
                                                          self.map_size[1] - new_height:self.map_size[1]] != 0)):
                self.mat_logic[spawn_x:spawn_x + new_width, self.map_size[1] - new_height:self.map_size[1]] = 2 * new_blocks_mask
                self.mat_color[spawn_x:spawn_x + new_width, self.map_size[1] - new_height:self.map_size[1]] = new_blocks_color * new_blocks_mask
            else:
                self.game_over = True

        def pack_spawn():
            block_spawn(self.pack[self.pack_no])
            self.pack_no += 1
            if self.pack_no == 7:
                self.pack_no = 0
                np.random.shuffle(self.pack)

            self.next_block_no = self.pack[self.pack_no]
            self.graphic_step()
            
            
        [n_eliminated,block_falled] = self.mat_iter()
        self.game_strategy.get_score(n_eliminated)
        if block_falled or self.game_step_count == 0:
            pack_spawn()
        self.graphic_step()
        self.game_step_count += 1

    def _get_falling_blocks(self, need_utils = False):
        falling_blocks_coord = np.where(self.mat_logic == 2)
        falling_blocks = []
        
        for i in range(len(falling_blocks_coord[0])):
            falling_blocks.append(np.array([p[i] for p in falling_blocks_coord]))
        if not need_utils:
            return falling_blocks
        else:
            x_min = self.map_size[0] + 1
            y_min = self.map_size[1] + 1
            x_max = -1
            y_max = -1
            for f_block in falling_blocks:
                x_min = min(f_block[0],x_min)
                x_max = max(f_block[0],x_max)
                y_min = min(f_block[1],y_min)
                y_max = max(f_block[1],y_max)
            color = self.mat_color[f_block[0],f_block[1]]
            return [falling_blocks,x_min,x_max,y_min,y_max,color]

    def block_slide(self,direction):
        if(direction == 0):
            return
        
        [falling_blocks,x_min,x_max,y_min,y_max,color] = self._get_falling_blocks(need_utils=True)
        
        if x_max + direction < self.map_size[0] and x_min + direction >= 0:
            falling_mask_logic = self.mat_logic[x_min:x_max+1,y_min:y_max+1]
            [w,h] = falling_mask_logic.shape
            if not np.any(np.logical_and(falling_mask_logic == 2, 
                                         self.mat_logic[x_min+direction:x_min+w+direction,y_max-h+1:y_max+1] == 1)):
                for f_block in falling_blocks:
                    self.mat_logic[f_block[0],f_block[1]] = self.mat_color[f_block[0],f_block[1]] = 0
                for f_block in falling_blocks:
                    self.mat_logic[f_block[0] + direction,f_block[1] ] = 2
                    self.mat_color[f_block[0] + direction,f_block[1]] = color
                self.graphic_step()
    

    def block_rotate(self,direction):
        if(direction == 0):
            return
        
        [falling_blocks,x_min,x_max,y_min,y_max,color] = self._get_falling_blocks(need_utils=True)
        falling_mask_logic = np.rot90(self.mat_logic[x_min:x_max+1,y_min:y_max+1],direction).copy()
        falling_mask_color = np.rot90(self.mat_color[x_min:x_max+1,y_min:y_max+1],direction).copy()

        [w,h] = falling_mask_logic.shape
        if x_min+w <= self.map_size[0] and y_max+1 < self.map_size[1]:
            for f_block in falling_blocks:
                self.mat_logic[f_block[0],f_block[1]] = self.mat_color[f_block[0],f_block[1]] = 0
            if not np.any(np.logical_and(falling_mask_logic == 2, self.mat_logic[x_min:x_min+w,y_max-h+1:y_max+1] == 1)):
                self.mat_logic[x_min:x_min+w,y_max-h+1:y_max+1] = falling_mask_logic
                self.mat_color[x_min:x_min+w,y_max-h+1:y_max+1] = falling_mask_color
                self.graphic_step()

    def main_thread(self):
        # 首先启动后端
        t_backend = threading.Thread(target=self.backend.run)
        t_backend.start()
        while True:
            if not self.game_running:
                continue # 高速忙等，确保收到后端信息立刻开始
            self.game_grapic_init()
            self.backend_ctrl_param_init()
            if self.is_multiplayer:
                self.game_round() # 多人模式只开一局
            else:
                while self.game_running:
                    self.game_round() # 单人模式在收到停止信号之前一直进行

    def game_round(self):
        self.game_strategy.reset()
        def show_tip():
            self.win.flip()
            operation_tip_text = self.game_strategy.multi_operation_tip if self.is_multiplayer else self.game_strategy.single_operation_tip
            score_tip_text = self.game_strategy.multi_score_tip if self.is_multiplayer else self.game_strategy.single_score_tip
            visual.TextStim(height = 0.04,win=self.win, text=operation_tip_text, pos=(-0.5,0.2), color=(1, 1, 1)).draw()
            if self.is_multiplayer:
                visual.TextStim(height = 0.04,win=self.win, text=self.game_strategy.get_multi_player_role_tip(self.backend.task), pos=(-0.5,0), color=(1, 1, 1)).draw()
            visual.TextStim(height = 0.04,win=self.win, text=score_tip_text, pos=(-0.5,-0.2), color=(0.9, 0.9, 1)).draw()
            self.win.flip()
            core.wait(read_tip_time)
            self.win.flip()

        def immed_graphic_update():
            if self.slide_direction != 0:
                self.block_slide(self.slide_direction)    
                self.slide_direction = 0             
            if self.rotate_direction != 0:
                self.block_rotate(self.rotate_direction)
                self.rotate_direction = 0   
        # 设置种子，在多人模式下使得种子相同
        seed = self.seed if self.is_multiplayer else np.random.randint(0,233333) 
        np.random.seed(seed)

        show_tip()
        while not self.game_over:
            t_begin = core.getTime()
            if not self.is_multiplayer:
                # 单人模式，自行计时
                self.game_update_flag = core.getTime() - t_begin >= step_time
            else:
                # 多人模式，响应按键事件回调设定的flag
                immed_graphic_update()
            while not self.game_update_flag:
                self.backend.get_key_status()
                # 等待到达更新时间
                if self.space_pressed:
                    self.game_update_flag = True
                    self.space_pressed = False
                    break 
                if not self.is_multiplayer:
                    # 单人模式，自行更新计时
                    self.game_update_flag = core.getTime() - t_begin >= step_time
                immed_graphic_update()

            if self.game_update_flag:
                self.game_step()
                self.game_update_flag = False
            
            
    def mat_iter(self):

        def block_touchdown():
            falling_blocks = np.where(self.mat_logic == 2)
            self.mat_logic[falling_blocks] = 1

        def block_eliminate():
            row_sums = np.sum(self.mat_logic == 1,axis=0)
            full_rows = np.where(row_sums == self.map_size[0])[0]
            rows_eliminated = len(full_rows)
            if rows_eliminated > 0:
                non_full_rows = np.where(row_sums != self.map_size[0])[0]
                new_logic = np.zeros_like(self.mat_logic)
                new_color = np.zeros_like(self.mat_color)

                new_logic[:,0:len(non_full_rows)] = self.mat_logic[:,non_full_rows]
                new_color[:,0:len(non_full_rows)] = self.mat_color[:,non_full_rows]

                self.mat_logic = new_logic
                self.mat_color = new_color

            return rows_eliminated
        
        falling_blocks = self._get_falling_blocks()
        if len(falling_blocks) > 0:
            # 检测碰撞
            for f_block in falling_blocks:
                if f_block[1] == 0 or self.mat_logic[f_block[0],f_block[1] -1] == 1:
                    block_touchdown()
                    n_eliminated = block_eliminate()
                    return n_eliminated,True
            # 下落一格
            color = self.mat_color[f_block[0],f_block[1]]
            for f_block in falling_blocks:
                self.mat_logic[f_block[0],f_block[1]] = self.mat_color[f_block[0],f_block[1]] = 0
            for f_block in falling_blocks:
                self.mat_logic[f_block[0],f_block[1] -1] = 2
                self.mat_color[f_block[0],f_block[1] -1] = color

        return 0,False

if __name__ == '__main__':
    game = Trtris_map()
    game.main_thread()