from psychopy import visual, core, event, monitors
import numpy as np

color_map = {0:'white',1:'red',2:'blue'}

class Trtris_map:
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
        self.gamespeed = 0.5
    
    def game_step(self):
        self.mat_iter()
        for i in range(0,self.map_size[0]):
            for j in range(0,self.map_size[1]):
                self.mat_render[i][j].setColor(color_map[self.mat_color[i,j]])
                self.mat_render[i][j].draw()
        self.win.flip()
        core.wait(self.gamespeed)
        
    
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
            
        falling_blocks_coord = np.where(self.mat_logic == 2)
        falling_blocks = []
        
        for i in range(len(falling_blocks_coord[0])):
            falling_blocks.append(np.array([p[i] for p in falling_blocks_coord]))
        print(falling_blocks)
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
for i in range(9):
    map.mat_color[i,0] = 1
    map.mat_logic[i,0] = 1

map.mat_color[9,5] = 2
map.mat_logic[9,5] = 2

for i in range(15):
    map.game_step()