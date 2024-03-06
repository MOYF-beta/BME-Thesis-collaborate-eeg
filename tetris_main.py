import argparse
from psychopy import visual, core, event, monitors
import yaml
from tetris_shape import tetris_shapes,tetris_color
import numpy as np
from numba import jit
class Trtris_map:

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

    def __init__(self,
                 map_size = (10,20),win_shape = (800,800),
                 game_zone_width = 0.7, margin = 0.1) -> None:
        self.win = visual.Window(size=win_shape, winType='pyglet')
        self.map_size = map_size
        self.mat_render = []
        self.mat_logic = np.zeros(map_size,dtype=np.int8)
        self.mat_color = np.zeros(map_size,dtype=np.int8)
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
        self.game_speed_text = visual.TextStim(win=self.win, text='Speed: 0.5', pos=(0.6, 0.2-rect_size*2), color=(1, 1, 1))

        self.game_score = 0
        self.gamespeed = 1
        self.game_over = False
        self.pack_no = 0
        self.pack = np.array(range(7),dtype=np.int8)
        self.game_step_count = 0
        self.spawn_flag = False
        self.next_block_no = int(self.pack[0])

        self.key_timestamps = []

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

        self.game_score_text.text = f'Score: {self.game_score}'
        self.game_speed_text.text = f'Speed: {self.gamespeed}'

        self.gameplay_area.draw()
        self.preview_area.draw()
        self.next_block_text.draw()
        self.game_score_text.draw()
        self.game_speed_text.draw()
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
                self.spawn_flag = True
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
            
            
        [new_score,block_falled] = self.mat_iter()
        self.game_score += new_score
        self.gamespeed = self.game_score // 5 + 1
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
        t_0 = core.getTime()
        while not self.game_over:
            t_begin = core.getTime()
            iter_time = 1/(np.sqrt(self.gamespeed)+1)
            while core.getTime() - t_begin < iter_time:
                if not self.spawn_flag:
                    break
                slide_direction = 0
                rotate_direction = 0
                keys_pressed = event.getKeys()
                if len(keys_pressed) > 0:
                    self.key_timestamps.append({"keys": keys_pressed, "time": core.getTime() - t_0})
                if 'z' in keys_pressed:
                    slide_direction -= 1
                if 'x' in keys_pressed:
                    slide_direction += 1
                if 'comma' in keys_pressed: # <
                    rotate_direction += 1
                if 'period' in keys_pressed: # >
                    rotate_direction -= 1
                if 'space' in keys_pressed: 
                    self.spawn_flag = False
                self.block_slide(slide_direction)
                self.block_rotate(rotate_direction) 
            self.game_step()
        print(self.key_timestamps)
        with open("key_timestamps.yaml", "w") as file:
            yaml.dump(self.key_timestamps, file)
        
    def main_thread_replay(self):
        with open("key_timestamps.yaml", "r") as file:
            key_timestamps = yaml.load(file, Loader=yaml.FullLoader)
            print(key_timestamps)
            idx = 0
            t_0 = core.getTime()
            entry = key_timestamps[idx]
            keys = entry["keys"]
            target_time = entry["time"]
            while not self.game_over:
                t_begin = core.getTime()
                iter_time = 1/(np.sqrt(self.gamespeed)+1)

                while core.getTime() - t_begin < iter_time:
                    if not self.spawn_flag:
                        break
                    if(core.getTime() - t_0) > target_time:
                        slide_direction = rotate_direction = 0
                        if 'z' in keys:
                            slide_direction += -1
                        if 'x' in keys:
                            slide_direction += 1
                        if 'comma' in keys:  # <
                            rotate_direction += 1
                        if 'period' in keys:  # >
                            rotate_direction += -1
                        if 'space' in keys:
                            self.spawn_flag = False
                        self.block_slide(slide_direction)
                        self.block_rotate(rotate_direction)
                        idx += 1
                        entry = key_timestamps[idx]
                        keys = entry["keys"]
                        target_time = entry["time"]

                self.game_step()
                    
    
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
                    score = block_eliminate()
                    score = score ** 2
                    return score,True
            # 下落一格
            color = self.mat_color[f_block[0],f_block[1]]
            for f_block in falling_blocks:
                self.mat_logic[f_block[0],f_block[1]] = self.mat_color[f_block[0],f_block[1]] = 0
            for f_block in falling_blocks:
                self.mat_logic[f_block[0],f_block[1] -1] = 2
                self.mat_color[f_block[0],f_block[1] -1] = color

        return 0,False


def main(start_mode):
    map = Trtris_map()
    if start_mode == 'normal':
        map.main_thread()
    elif start_mode == 'replay':
        map.main_thread_replay()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='游戏模式')
    parser.add_argument('--mode', choices=['normal', 'replay'], default='normal', help='启动模式：正常模式或回放模式')

    args = parser.parse_args()

    main(args.mode)