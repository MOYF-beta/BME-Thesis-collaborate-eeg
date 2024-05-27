# TODO 4、添加游戏规则：A为fast_pace组，按空格+1，消1行+10，无倍率。B为low_pace组，消n行+n方10，按空格不加分

class game_strategy:
    
    def __init__(self) -> None:
        pass
    
    def get_score(self,cur_score:int,col_eliminated:int):
        # 计算得分
        new_score = cur_score + col_eliminated
        return new_score

    def get_begin_tip_text(self):
        # 显示游戏规则等提示
        return "未实现"
    

class group_A(game_strategy):
    
    pass


class group_B(game_strategy):

    pass
    
class cross_group_collaborate(game_strategy):

    pass