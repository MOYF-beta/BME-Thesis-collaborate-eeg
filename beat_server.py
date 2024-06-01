import cmd
import sys
import threading
import numpy as np
from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

import time
import net_config
from twisted.internet import reactor, protocol
from twisted.internet.protocol import DatagramProtocol
import json

from psychopy import core

class beat_server(cmd.Cmd):
    
    class player:

        id = 0

        def __init__(self,ip) -> None:
            self.ip = ip
            self.group = None
            self.task = None
            self.id = beat_server.player.id
            beat_server.player.id = beat_server.player.id + 1
        
        def get_info(self):
            return (self.ip,self.group,self.task)

        prompt = '> '
        intro = "团队协作范式控制台 输入‘?’ 显示帮助"

    def __init__(self, completekey: str = "tab", stdin= sys.stdin, stdout = sys.stdout) -> None:
        super().__init__(completekey, stdin, stdout)
        self.players:list[beat_server.player] = []
        self.console = Console()
        self.twisted_server = beat_server.UDP_ctrl_client(self.players)
        reactor_thread = threading.Thread(target=self.start_reactor)
        reactor_thread.start()
        
    def start_reactor(self):
        reactor.listenUDP(net_config.server_port, self.twisted_server)
        reactor.run(installSignalHandlers=False)  # Avoid conflict with the main thread signal handling

    def run(self):
        # Create a thread to run the reactor
        reactor_thread = threading.Thread(target=self.start_reactor)
        reactor_thread.start()
    def do_ag(self, line):
        tokens = line.split()
        try:
            player_id = int(tokens[0])
        except:
            self.console.print(Text("玩家id应该是个数字", style="bold red"))
            return
        group = tokens[1].upper()
        have_player_flag = False
        if group != 'A' and group.upper() != 'B':
            warning_text = Text("分组只能指派 A、B", style="bold red")
            self.console.print(warning_text)
            return
        p = None
        for player in self.players:
            if player.id == player_id:
                p = player
                player.group = group.upper()
                have_player_flag = True
                break
        if not have_player_flag:
            warning_text = Text("没有这个玩家", style="bold red")
            self.console.print(warning_text)
            return
        
        
        self.twisted_server.arrange_group(self.players)
        self.console.print(f'已为{player_id}分组为{group}')

    def do_at(self, line):
        tokens = line.split()
        try:
            player_id = int(tokens[0])
        except:
            self.console.print(Text("玩家id应该是个数字", style="bold red"))
        task = tokens[1].lower()
        have_player_flag = False
        p = None
        for player in self.players:
            if player.id == player_id:
                p = player
                have_player_flag = True
                break
        if not have_player_flag:
            warning_text = Text("没有这个玩家", style="bold red")
            self.console.print(warning_text)
            return
        if task.lower() != 'rotate' and task.lower() != 'slide':
            warning_text = Text("分组只能指派 slide、rotate", style="bold red")
            self.console.print(warning_text)
            return
        p.task = task.lower()
        self.twisted_server.arrange_task(self.players)
        self.console.print(f'已为{player_id}分配合作任务为{task}')

    def do_ss(self, line):
        # start single
        self.twisted_server.start_single()
        

    def do_sm(self, line):
        # start multi
        self.twisted_server.start_multi()
        

    def do_es(self, line):
        # exit single
        self.twisted_server.end_single()
        

    def do_em(self, line):
        # exit multi
        self.twisted_server.end_multi()
        

    def do_lp(self, line):
        # list players
        table = Table(title="玩家")
        table.add_column("ID", justify="center", style="cyan")
        table.add_column("IP", justify="center", style="white")
        table.add_column("Group", justify="center", style="magenta")
        table.add_column("Task", justify="center", style="green")
        for p in self.players:
            table.add_row(str(p.id), p.ip, p.group or "未指定", p.task or "未指定")
        self.console.print(table)
        

    class UDP_ctrl_client(DatagramProtocol):
        def __init__(self, players,udp_group = '224.0.0.1'):
            self.players :list[beat_server.player] = players
            self.server_port = net_config.server_port
            self.ctrl_port = net_config.ctrl_port
            self.udp_group = udp_group
            self.console = Console()
            self.multiplayer_running : bool = False
            self.beat_thread : threading.Thread = None
            self.sync_falling_block_thread : threading.Thread = None
            self.newest_falling_blocks = np.zeros(net_config.map_size)
            self.pack_timestamp = 0
            self.new_falling_block_flag = False
            self.about_to_sync = False
            self.sync_time = 0.005

        def reported_ip_to_beat_server(self):
            while not self.reported_ip:
                self.send_data({})
                time.sleep(0.5)

        def startProtocol(self):
            pass

        def datagramReceived(self, data, addr):
            client_ip,_ = addr
            clients_addr = [client.ip for client in self.players]
            if self.multiplayer_running:
                if self.about_to_sync:
                    return # 在即将同步下落时不发送按键事件
                for player in self.players:
                    try:
                        # 先进行一下json格式校验在转发
                        data_dict = json.loads(data.decode('utf-8'))
                        if 'f' in data_dict: # 空格按键事件，直接转发
                            pass#self._send_data(player.ip, data)
                        # TODO 改为仅在下落的那一刻更新 s-> 等待收到前端blocks -> 收到一个后立即向所有前端发送blocks
                        # 对前端，正常渲染，收到s后先上传，然后等待收到 blocks后设置自身的falling block，然后再在逻辑上计算
                        if 'b' in data_dict: # 来自客户端的下落方块更新
                            newest_falling_blocks = self.get_falling_block_coords(data_dict['b'])
                            timestamp = data_dict['t']
                            if timestamp >= self.pack_timestamp and not np.array_equal(self.newest_falling_blocks,newest_falling_blocks):
                                self.send_data_to_player_s(self.players,data)
                                self.pack_timestamp = timestamp
                                self.newest_falling_blocks = newest_falling_blocks
                                core.wait(0.05)
                                self.send_data_to_player_s(self.players,data)

                    except:
                        self.console.log(f"unknow msg : {data}")
            else:
                try:
                    data_dict = json.loads(data.decode('utf-8'))
                    if client_ip not in clients_addr and 'find' in data_dict and data_dict['find'] == net_config.discover_keyword:
                        player = beat_server.player(client_ip)
                        self.players.append(player)
                        self._send_data(client_ip, '{"ack":1}')
                        self.console.log(f'发现玩家 {player.id} @ {addr}')
                except:
                    self.console.print(Text(f"{addr}:{data.decode('utf-8')}", style="bold red"))
            
            
        def _send_data(self,ip,data):
            if not isinstance(data,bytes):
                data = data.encode('utf-8')
            self.transport.write(data,(ip,self.ctrl_port))

        def send_data_to_player_s(self,player_s,data):
            def send(player_s,data):
                if not isinstance(player_s, list):
                    player_s = [player_s]
                for player in player_s:
                    self._send_data(player.ip,data)
            t = threading.Thread(target=send,args=[player_s,data])
            t.start()
        
        def rich_warning(self,msg):
            message = msg
            warning_text = Text(message, style="bold red")
            panel = Panel(warning_text, title="Warning", border_style="red")
            self.console.print(panel)

        '''初始化，客户端发现、分组'''
        def arrange_group(self,players):
            if not isinstance(players, list):
                players = [players]
            for player in players:
                if player.group is not None:
                    self.send_data_to_player_s(player,json.dumps({
                        'op':'ag',
                        'group':player.group}))
        
        def arrange_task(self,players):
            for player in players:
                if player.task is not None:
                    self.send_data_to_player_s(player,json.dumps({
                        'op':'at',
                        'task':player.task}))

        '''单人游戏控制'''
        def start_single(self):
            for player in self.players:
                if player.group is None:
                    self.rich_warning("警告：有玩家未分组")
                    return
            self.console.print(f'{[player.ip for player in self.players]}单人模式')
            
            for player in self.players:
                self.send_data_to_player_s(player,json.dumps({
                        'op':'ss'}))
                        
            
            

        def end_single(self):
            for player in self.players:
                self.send_data_to_player_s(player,json.dumps({
                        'op':'es'}))
            self.console.print(f'{[player.ip for player in self.players]}停止单人模式')

        '''多人游戏控制'''
        def start_multi(self):
            for player in self.players:
                if player.group is None:
                    self.rich_warning("警告：有玩家未分组")
                    return
                if player.task is None:
                    self.rich_warning("警告：有玩家未指配task")
                    return
            self.send_data_to_player_s(self.players,json.dumps({
                'op':'sm',
                'ip':[player.ip for player in self.players],
                'seed':np.random.randint(0,23333)
            }))
            self.console.print(f'{[player.ip for player in self.players]}多人模式')
            time.sleep(net_config.read_tip_time)
            self.beat_thread = threading.Thread(target=self.sync_beat)
            #self.sync_falling_block_thread = threading.Thread(target=self.sync_falling_block)
            self.multiplayer_running = True
            self.beat_thread.start()
            #self.sync_falling_block_thread.start()
            self.console.print(f'{[player.ip for player in self.players]}开始运行')

        def sync_beat(self):
            '''
            {"k":[...]}
            k是按键事件，z=1,x=2,<=3,>=4,space=5
            {"s":1}
            s是按键同步
            '''
            while self.multiplayer_running:
                time = core.getTime()
                while core.getTime() - time <= net_config.step_time - self.sync_time:
                    core.wait(0.001)
                # 即将同步，禁止发送按键（直接丢弃客户端收到的包）
                self.about_to_sync = True
                self.send_data_to_player_s(self.players,json.dumps({
                    's':1
                }))
                core.wait(self.sync_time) # 确保客户端已经执行了下落操作。
                self.about_to_sync = False
        
        def sync_falling_block(self):
            '''
            以一定速率向客户端发送最新的游戏局面
            '''
            while self.multiplayer_running:
                if self.about_to_sync:
                    continue
                core.wait(net_config.update_freq)
                if self.newest_falling_blocks is not None:
                    data_str = json.dumps({'f':self.newest_falling_blocks})
                    self.send_data_to_player_s(self.players,data_str)
                    self.newest_falling_blocks = None
                    # TODO 添加一个对比，如果没有变化就不发送

        def get_falling_block_coords(self,data):
            mat = np.zeros(net_config.map_size)
            for i in range(len(data)//2):
                mat[data[i*2],data[i*2+1]] = 1
            return mat
        
        def end_multi(self):
            self.send_data_to_player_s(self.players,json.dumps({
                'op':'em'
            }))
            self.multiplayer_running = False
            if self.beat_thread is not None:
                self.beat_thread = None
            self.console.print(f'{[player.ip for player in self.players]}停止多人模式')

if __name__ == '__main__':
    server = beat_server()
    server.cmdloop()