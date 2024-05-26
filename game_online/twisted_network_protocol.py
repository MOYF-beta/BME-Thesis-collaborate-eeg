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
        self.key_service = None
        self.udp_client = None

    def run_ctrl_transport(self):
        self.udp_client = game_net.UDP_ctrl_client(self.ctrl_handler)
        reactor.listenUDP(net_config.ctrl_port, self.udp_client)
        reactor_thread = threading.Thread(target=reactor.run)
        reactor_thread.start()
        self.udp_client.reported_ip_to_beat_server()

    def run_key_event_transport(self,task:str,host_ip:str):
        assert task in ['slide' ,'rotate']
        # reactor.stop()
        # reactor.__init__() # 重置reactor
        # self.udp_client = game_net.UDP_ctrl_client(self.ctrl_handler)
        # reactor.listenUDP(net_config.ctrl_port, self.udp_client) # 重新添加UDP任务 BUG 端口似乎还没有释放
        reactor.disconnectAll()
        reactor.__init__()
        reactor.listenUDP(net_config.ctrl_port, self.udp_client)
        factory = game_net.TCP_key_protocol_Factory(self.key_handler)
        if task == 'slide':
            time.sleep(1) # 稍微等下对面按键事件服务器创建
            reactor.connectTCP(host_ip,self.key_event_port, factory)
        else:
            reactor.listenTCP(self.key_event_port, factory)
        reactor_thread = threading.Thread(target=reactor.run)
        reactor_thread.start()
        time.sleep(1)
        self.key_service = factory.get_client()
        assert self.key_service is not None, "无法连接另一位玩家。请检查网络连通性以及防火墙配置，放行tcp 8002端口"
        self.key_service_on = True
    
    def send_key(self,keys):
        self.key_service.send_data(json.dumps(keys))
    
    def resopnd_beat_server(self,data):
        self.udp_client.send_data(data)
        
    class UDP_ctrl_client(DatagramProtocol):
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
            # self.transport.joinGroup('224.0.0.1')
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
    class TCP_key_protocol(protocol.Protocol):
        def __init__(self, callback:Callable[[dict],None],factory):
            self.callback = callback
            factory.client = self

        def connectionMade(self):
            pass

        def dataReceived(self, data):
            data_dict = json.loads(data.decode('utf-8'))
            self.callback(data_dict)

        def send_data(self,data):
            self.transport.write(str(data).encode('utf-8'))

    
    class TCP_key_protocol_Factory(protocol.ClientFactory):
        def __init__(self, callback:Callable[[dict],None]):
            self.callback = callback
            self.client:game_net.TCP_key_protocol = None
        def get_client(self):
            return self.client
        def buildProtocol(self, callback):
            self.client = game_net.TCP_key_protocol(callback,self)
            return self.client

        def clientConnectionFailed(self, connector, reason):
            print("Connection failed.")
            reactor.stop()

        def clientConnectionLost(self, connector, reason):
            print("Connection lost.")
            reactor.stop()