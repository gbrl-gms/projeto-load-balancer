from mininet.net import Containernet
from mininet.node import Controller, Docker, OVSSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info

def topology():
    net = Containernet(controller=Controller)

    info('*** Adding Controller')
    net.addController('c0')

    info('*** Adding Load Balancer')
    load_b = net.addDocker('load_b', ip='10.0.0.20', dimage='projeto-load-balancer-load_balancer', network_mode='none')

    info('*** Adding Nginx servers')
    srv_a = net.addDocker('srv_a', ip='10.0.0.21', dimage='projeto-load-balancer-servidor_a', network_mode='none')
    srv_b = net.addDocker('srv_b', ip='10.0.0.22', dimage='projeto-load-balancer-servidor_b', network_mode='none')

    info('*** Adding client Node')
    client = net.addDocker('client', ip = '10.0.0.10', dimage="curlimages/curl:latest")

    info('*** Linking topology')
    net.addLink(srv_a,load_b)
    net.addLink(srv_b,load_b)
    net.addLink(client,load_b)

    info('*** Starting the network')
    net.start()

    info('*** Starting Mininet CLI')
    CLI(net)

    info('*** Stopping the network')
    net.stop()

# ababa

if __name__ == '__main__':
    setLogLevel('info')
    topology()
