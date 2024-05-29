import threading
import time
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
class UDP_ctrl_client(DatagramProtocol):
    def __init__(self, server_port=8000, udp_group='224.0.0.1',):
        self.server_port = server_port
        self.udp_group = udp_group

    def startProtocol(self):
        self.transport.joinGroup(self.udp_group, '10.128.163.25')

    def datagramReceived(self, data, addr):
        print(addr)
        print(data.decode('utf-8'))

    def _send_data(self, ip, data):
        self.transport.write(data.encode('utf-8'), (ip, self.server_port))

        
def start_reactor(server):
    reactor.listenMulticast(8000, server)
    reactor.run(installSignalHandlers=False)

if __name__ == '__main__':
    twisted_server = UDP_ctrl_client()
    
    reactor_thread = threading.Thread(target=start_reactor,args=[twisted_server])
    reactor_thread.start()
    time.sleep(1)
    twisted_server._send_data('224.0.0.1',"hello?")

