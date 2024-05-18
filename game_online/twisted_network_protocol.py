import time
from typing import Callable
from twisted.internet import reactor, protocol
from twisted.internet.protocol import DatagramProtocol
import json

'''twisted挺麻烦的，但自己写异步感觉更麻烦，呜'''

class game_net:
    
    def __init__(self,ctrl_handler:Callable[[dict],None],
                  key_handler:Callable[[dict],None],
                    ctrl_port = 8000, key_event_port = 8001) -> None:
        self.ctrl_handler = ctrl_handler
        self.key_handler = key_handler
        self.ctrl_port = ctrl_port
        self.key_event_port = key_event_port
        self.key_service = None

    def run_ctrl_transport(self):
        reactor.listenMulticast(self.ctrl_port, game_net.UDP_ctrl_client(self.ctrl_handler,self.ctrl_handler))
        reactor.run()

    def run_key_event_transport(self,task:str,host:str):
        assert task in ['slide' ,'rotate']
        reactor.stop()
        reactor.__init__() # 重置reactor
        reactor.listenMulticast(self.ctrl_port, game_net.UDP_ctrl_client(self.ctrl_handler,self.ctrl_handler)) # 重新添加UDP任务
        if task == 'slide':
            factory = game_net.TCP_key_client_Factory(self.key_handler)
            reactor.connectTCP(host, self.key_event_port,factory)
            self.key_service = factory.get_client()
            assert self.key_service is not None
            time.sleep(1) # 稍微等下对面按键事件服务器创建
        else:
            factory = game_net.TCP_key_server_Factory(self.key_handler)
            reactor.listenTCP(self.key_event_port, factory)
            self.key_service = factory.get_client()
            assert self.key_service is not None

        reactor.run()
        self.key_service_on = True
    
    def send_key(self,keys):
        self.key_service.send_data(json.dumps(keys))
        

    # 使用：reactor.listenMulticast(self.ctrl_port, game_net.UDP_ctrl_client())
    class UDP_ctrl_client(DatagramProtocol):
        def __init__(self, callback:Callable[[dict],None], server_port):
            self.callback = callback
            self.server_ip = None
            self.server_port = server_port

        def startProtocol(self):
            self.transport.joinGroup('224.0.0.1')
        def datagramReceived(self, data, addr):
            self.server_ip,_ = addr
            data_dict = json.loads(data.decode('utf-8'))
            self.callback(data_dict)
        def send_data(self,data):
            assert self.server_addr is not None
            self.transport.write(str(data),(self.server_ip,self.server_port))

    # 按键事件交换服务器
    class TCP_key_server(protocol.Protocol):
        def __init__(self, callback:Callable[[dict],None]):
            self.callback = callback

        def dataReceived(self, data):
            data_dict = json.loads(data.decode('utf-8'))
            self.callback(data_dict)

        def send_data(self,data):
            self.transport.write(str(data))

    # 按键事件交换客户端
    class TCP_key_client(protocol.Protocol):
        def __init__(self, callback:Callable[[dict],None]):
            self.callback = callback

        def connectionMade(self):
            pass

        def dataReceived(self, data):
            data_dict = json.loads(data.decode('utf-8'))
            self.callback(data_dict)

        def send_data(self,data):
            self.transport.write(str(data))
    
    class TCP_key_server_Factory(protocol.Factory):
        def __init__(self, callback:Callable[[dict],None]):
            self.callback = callback
            self.client:game_net.TCP_key_client = None
        def get_client(self):
            return self.client
        def buildProtocol(self, callback):
            self.client = game_net.TCP_key_client(callback)
            return self.client
    
    class TCP_key_client_Factory(protocol.ClientFactory):
        def __init__(self, callback:Callable[[dict],None]):
            self.callback = callback
            self.client:game_net.TCP_key_client = None
        def get_client(self):
            return self.client
        def buildProtocol(self, callback):
            self.client = game_net.TCP_key_client(callback)
            return self.client

        def clientConnectionFailed(self, connector, reason):
            print("Connection failed.")
            reactor.stop()

        def clientConnectionLost(self, connector, reason):
            print("Connection lost.")
            reactor.stop()