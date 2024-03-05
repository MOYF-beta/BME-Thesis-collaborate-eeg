from psychopy import visual, core, event, monitors
from tetris_shape import tetris_shapes,tetris_color
import numpy as np
from numba import jit
class Trtris_map:

    def _generate_positions(self, map_size, rect_size, margin):
        positions = []
        for i in range(map_size[0]):
            for j in range(map_size[1]):
                x = margin + -1 + i * rect_size + 0.5 * rect_size
                y = -1 + j * rect_size + 0.5 * rect_size
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
        for i in range(0,map_size[0]):
            new_col = []
            for j in range(0,map_size[1]):
                rect = visual.Rect(self.win, width=rect_size, height=rect_size,
                                    fillColor='white',lineColor='black')
                rect_cent_x =  margin + -1 + i * rect_size + 0.5 * rect_size
                rect_cent_y = -1 + j * rect_size + 0.5 * rect_size
                rect.setPos((rect_cent_x,rect_cent_y))
                new_col.append(rect)
            self.mat_render.append(new_col)
        nElements = map_size[0] * map_size[1]
        self.stim_array = visual.ElementArrayStim(win=self.win, 
                                          nElements=nElements, 
                                          elementTex=None, 
                                          elementMask="rect", 
                                          sizes=rect_size, 
                                          xys=self._generate_positions(map_size, rect_size, margin), 
                                          colors=[0,0,0])
        self.gamespeed = 0.5
        self.game_over = False


    def graphic_step(self):
        # 更新颜色
        colors = [tetris_color[self.mat_color[i, j]] 
                  for i in range(self.map_size[0]) 
                  for j in range(self.map_size[1])]
        self.stim_array.colors = colors
        # 绘制
        self.stim_array.draw()
        self.win.flip()
        
    def game_step(self):
        self.mat_iter()
        self.graphic_step()

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
        for f_block in falling_blocks:
            self.mat_logic[f_block[0],f_block[1]] = self.mat_color[f_block[0],f_block[1]] = 0

        if not np.any(np.logical_and(falling_mask_logic == 2, self.mat_logic[x_min:x_min+w,y_max-h+1:y_max+1] == 1)):
            self.mat_logic[x_min:x_min+w,y_max-h+1:y_max+1] = falling_mask_logic
            self.mat_color[x_min:x_min+w,y_max-h+1:y_max+1] = falling_mask_color
        self.graphic_step()


    def main_thread(self):
        self.block_spawn(1)
        while not self.game_over:
            t_begin = core.getTime()
            while core.getTime() - t_begin < self.gamespeed:
                slide_direction = 0
                rotate_direction = 0
                keys_pressed = event.getKeys()
                # if(len(keys_pressed)>0):
                #     print(keys_pressed)
                if 'z' in keys_pressed:
                    slide_direction -= 1
                if 'x' in keys_pressed:
                    slide_direction += 1
                if 'comma' in keys_pressed:#<
                    rotate_direction -= 1
                if 'period' in keys_pressed:#>
                    rotate_direction += 1
                self.block_slide(slide_direction)
                self.block_rotate(rotate_direction)
            self.game_step()


                    
        
    
    def block_spawn(self,shape_no):
        new_blocks_mask = tetris_shapes[shape_no]
        new_blocks_color = shape_no + 1
        [new_width,new_height] = new_blocks_mask.shape
        spawn_x = self.map_size[0] // 2 - new_width // 2

        self.mat_logic[spawn_x:spawn_x + new_width, self.map_size[1] - new_height:self.map_size[1]] = 2 * new_blocks_mask
        self.mat_color[spawn_x:spawn_x + new_width, self.map_size[1] - new_height:self.map_size[1]] = new_blocks_color * new_blocks_mask

        self.graphic_step()
    
    def mat_iter(self):

        def block_touchdown():
            falling_blocks = np.where(self.mat_logic == 2)
            self.mat_logic[falling_blocks] = 1

        def block_eliminate():
            # 在block_touchdown后不应该有值为2的区域了
            rows_eliminated = 0
            row_sums = np.sum(self.mat_logic == 1,axis=0)
            for j in range(len(row_sums)):
                if row_sums[j] == self.map_size[0]:
                    self.mat_logic[:,j:-1] = self.mat_logic[:,j+1:]
                    self.mat_color[:,j:-1] = self.mat_color[:,j+1:]
                    rows_eliminated += 1
            return rows_eliminated
        falling_blocks = self._get_falling_blocks()
        # print(falling_blocks)
        if len(falling_blocks) > 0:
            # 检测碰撞
            for f_block in falling_blocks:
                if f_block[1] == 0 or self.mat_logic[f_block[0],f_block[1] -1] == 1:
                    block_touchdown()
                    score = block_eliminate()
                    score = score ** 2
                    return score
            # 下落一格
            color = self.mat_color[f_block[0],f_block[1]]
            for f_block in falling_blocks:
                self.mat_logic[f_block[0],f_block[1]] = self.mat_color[f_block[0],f_block[1]] = 0
            for f_block in falling_blocks:
                self.mat_logic[f_block[0],f_block[1] -1] = 2
                self.mat_color[f_block[0],f_block[1] -1] = color

        return 0

        


map = Trtris_map()

map.main_thread()


# for j in range(7):
#     map.block_spawn(j)
#     for i in range(30):
#         map.game_step()