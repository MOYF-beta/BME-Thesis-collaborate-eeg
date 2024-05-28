import threading
import time
from typing import Callable
from twisted.internet import reactor, protocol
from twisted.internet.protocol import DatagramProtocol
import json
import net_config

'''twisted挺麻烦的，但自己写异步感觉更麻烦，呜'''

class twisted_game_networking:
    
    def __init__(self,data_handler:Callable[[dict],None]) -> None:
        self.data_handler = data_handler
        self.server_port = net_config.server_port
        self.key_event_port = net_config.p2p_port
        self.udp_ctrl = None
        self.init_stage = 0

    def run_ctrl_transport(self):
        if self.init_stage > 0:
            return
        self.udp_ctrl = twisted_game_networking.UDP_ctrl_protocol(self.data_handler)
        reactor.listenUDP(net_config.ctrl_port, self.udp_ctrl)
        reactor_thread = threading.Thread(target=reactor.run)
        reactor_thread.start()
        self.udp_ctrl.reported_ip_to_beat_server()
        self.init_stage = 1
    
    def send_key(self,keys):
        self.udp_ctrl.send_data(json.dumps(keys))
    
    class UDP_ctrl_protocol(DatagramProtocol):
        def __init__(self, callback:Callable[[dict],None]):
            self.callback = callback
            self.server_ip = net_config.server_ip
            self.server_port = net_config.server_port
            self.reported_ip = False

        def reported_ip_to_beat_server(self):
            while not self.reported_ip:
                self.send_data(json.dumps({'find':net_config.discover_keyword}))
                time.sleep(0.5)

        def handle_server_ack_msg(self,data,addr):
            # 处理服务器发来的ack，确定已被服务器发现
            self.server_ip,_ = addr
            try:
                data_dict = json.loads(data.decode('utf-8'))    
                if 'ack' in data_dict.keys(): # 服务器单播确认已经找到ip
                    print(f'server @ {addr} found')
                    self.reported_ip = True
            except Exception as e:
                print(e)
            print(f"{addr}:{data}")
        
        def handle_server_game_msg(self,data):
            # 处理游戏中的信号，包含beat与按键信号
            try:
                data_dict = json.loads(data.decode('utf-8'))
                self.callback(data_dict)
            except:
                print(f"unknow msg:{data}")

        def startProtocol(self):
            pass

        def datagramReceived(self, data, addr):
            if not self.reported_ip:
                self.handle_server_ack_msg(data, addr)
            else:
                self.handle_server_game_msg(data)

        def send_data(self,data):
            assert self.server_ip is not None
            is_str = isinstance(data,str)
            is_byte = isinstance(data,str)
            if not is_str and not is_byte:
                data = json.dumps(data)
            elif is_str:
                data = data.encode('utf-8')
            self.transport.write(str(data).encode('utf-8'),(self.server_ip,self.server_port))