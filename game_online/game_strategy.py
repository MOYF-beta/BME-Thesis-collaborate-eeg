# TODO 4、添加游戏规则：A为fast_pace组，按空格+1，消1行+10，无倍率。B为low_pace组，消n行+n方10，按空格不加分

class game_strategy:
    # 游戏计分类
    def __init__(self) -> None:
        self.single_operation_tip = "单人模式：zx控制左右平移,<>控制旋转,单击空格立即下落一格\n该游戏有点难，您将在单人模式熟悉操作"
        self.multi_operation_tip = "多人模式：规则与单人模式相同，您将与另一个玩家联机协作\n"
        self.single_score_tip = "单人模式提示"
        self.multi_score_tip = "多人模式提示"
        self.score = 0
    
    @staticmethod
    def get_multi_player_role_tip(role:str):
        if role == 'slide':
            return "您的任务是左右移动方块,用zx操作（只有您能操作）\n单击空格立即下落一格（您和对方都能操作）\n对方负责控制<>按钮"
        elif role == 'rotate':
            return "您的任务是旋转方块,用<>操作（只有您能操作）,单击空格立即下落一格（您和对方都能操作）\n对方负责控制zx按钮"

    def get_score(self,col_eliminated:int):
        # 计算得分
        self.score = self.score + col_eliminated * 10

    def space_bouns(self):
        # 按下空格的额外奖励
        self.score = self.score + 1

class group_A(game_strategy):
    def __init__(self) -> None:
        self.single_score_tip = "每消除一行得10分，每使用一次空格下落1格额外得1分"
        self.multi_score_tip = "与单人模式相同。每消除一行得10分，每使用一次空格下落1格额外得1分"
        self.score = 0
    # fast_pace
    def get_score(self, col_eliminated: int):
        self.score = self.score + col_eliminated * 10
    
    def space_bouns(self):
        # 按下空格的额外奖励
        self.score = self.score + 1

class group_B(game_strategy):
    def __init__(self) -> None:
        self.single_score_tip = "一次消除n行得到n^2分，例如消除1行的1分，消除4行得16分"
        self.multi_score_tip = "与单人模式相同。一次消除n行得到n^2分，例如消除1行的1分，消除4行得16分"
        self.score = 0
    # fast_pace
    def get_score(self, col_eliminated: int):
        self.score = self.score + col_eliminated ** 2
    
    def space_bouns(self):
        # 按下空格的额外奖励
        self.score = self.score + 1
