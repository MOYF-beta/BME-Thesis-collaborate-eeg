import threading
import time
from typing import Callable
from twisted.internet import reactor, protocol
from twisted.internet.protocol import DatagramProtocol
import json
import net_config

'''twisted挺麻烦的，但自己写异步感觉更麻烦，呜'''

class game_net:
    
    def __init__(self,ctrl_handler:Callable[[dict],None],
                  key_handler:Callable[[dict],None]) -> None:
        self.ctrl_handler = ctrl_handler
        self.key_handler = key_handler
        self.server_port = net_config.server_port
        self.key_event_port = net_config.p2p_port
        self.udp_ctrl = None
        self.udp_key = None

    def run_ctrl_transport(self):
        self.udp_ctrl = game_net.UDP_ctrl_protocol(self.ctrl_handler)
        reactor.listenUDP(net_config.ctrl_port, self.udp_ctrl)
        reactor_thread = threading.Thread(target=reactor.run)
        reactor_thread.start()
        self.udp_ctrl.reported_ip_to_beat_server()

    def run_key_event_transport(self,task:str,host_ip:str):
        assert task in ['slide' ,'rotate']
        reactor.disconnectAll()
        reactor.__init__()
        self.udp_key = game_net.UDP_key_protocol(self.key_handler,host_ip)
        reactor.listenUDP(net_config.ctrl_port, self.udp_ctrl)
        reactor.listenUDP(net_config.p2p_port, self.udp_key)
        reactor_thread = threading.Thread(target=reactor.run)
        reactor_thread.start()
    
    def send_key(self,keys):
        self.udp_key.send_data(json.dumps(keys))
    
    def resopnd_beat_server(self,data):
        self.udp_ctrl.send_data(data)
        
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

        def startProtocol(self):
            pass

        def datagramReceived(self, data, addr):
            self.server_ip,_ = addr
            try:
                data_dict = json.loads(data.decode('utf-8'))
                if self.reported_ip:
                    self.callback(data_dict)
                elif 'ack' in data_dict.keys(): # 服务器单播确认已经找到ip
                    self.reported_ip = True
            except Exception as e:
                print(e)
            print(f"{addr}:{data}")

        def send_data(self,data):
            assert self.server_ip is not None
            self.transport.write(str(data).encode('utf-8'),(self.server_ip,self.server_port))

    # 按键事件交换协议
    class UDP_key_protocol(protocol.Protocol):
        def __init__(self, callback:Callable[[dict],None], other_player_ip):
            self.callback = callback
            self.other_player_ip = other_player_ip
        def startProtocol(self):
            pass
        def datagramReceived(self, data, addr):
            try:
                data_dict = json.loads(data.decode('utf-8'))
                self.callback(data_dict)
            except:
                print(f'err while decode key event{data}')

        def send_data(self,data):
            assert self.other_player_ip is not None
            self.transport.write(str(data).encode('utf-8'),(self.other_player_ip,net_config.p2p_port))

    