# TODO 4、添加游戏规则：A为fast_pace组，按空格+1，消1行+10，无倍率。B为low_pace组，消n行+n方10，按空格不加分

class game_strategy:
    # 游戏计分类
    def __init__(self) -> None:
        self.single_begin_tip_text = "单人模式提示"
        self.multi_begin_tip_text = "多人模式提示"
        self.score = 0
        pass
    
    def get_score(self,col_eliminated:int):
        # 计算得分
        new_score = self.score + col_eliminated * 10

    def space_bouns(self):
        # 按下空格的额外奖励
        self.score = self.score + 1

class group_A(game_strategy):
    pass

class group_B(game_strategy):
    pass
    
class cross_group_collaborate(game_strategy):
    pass