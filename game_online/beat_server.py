import cmd
from rich.table import Table
from rich.console import Console
class beat_server(cmd.Cmd):
    
    class player:
        def __init__(self,ip) -> None:
            self.ip = ip
            self.group = None
            self.task = None
        def get_info(self):
            return (self.ip,self.group,self.task)

        prompt = '> '
        intro = "团队协作范式控制台 输入‘?’ 显示帮助"

    def __init__(self, completekey: str = "tab", stdin: cmd.IO[str] | None = None, stdout: cmd.IO[str] | None = None) -> None:
        super().__init__(completekey, stdin, stdout)
        self.players:list[beat_server.player] = []
        self.console = Console()

    def do_ag(self, line):
        # arrange group
        pass

    def do_at(self, line):
        # arrange task
        pass

    def do_ss(self, line):
        # start single
        pass

    def do_sm(self, line):
        # start multi
        pass

    def do_es(self, line):
        # exit single
        pass

    def do_em(self, line):
        # exit multi
        pass

    def do_lp(self, line):
        # list players
        table = Table(title="玩家")
        table.add_column("IP", justify="center", style="cyan")
        table.add_column("Group", justify="center", style="magenta")
        table.add_column("Task", justify="center", style="green")
        for p in self.players:
            table.add_row(p.ip, p.group or "未指定", p.task or "未指定")
        self.console.print(table)
        

    class twisted_transport():
        '''用twisted处理网络的类'''
        def __init__(self) -> None:
            pass
        '''初始化，客户端发现、分组'''
        def arrange_group():
            pass # TODO 游戏开始时的分组

        def arrange_op():
            pass # TODO 分配旋转、平移

        '''单人游戏控制'''

        def start_single():
            pass

        def end_single():
            pass

        '''多人游戏控制'''

        def start_multi():
            pass

        def sync_beat():
            pass
        
        def end_multi():
            pass