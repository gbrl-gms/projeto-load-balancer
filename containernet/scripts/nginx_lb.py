from mininet.net import Containernet
from mininet.node import Controller, Docker, OVSSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from time import sleep

def topology():
    net = Containernet(controller=Controller)

    info('*** Adding Controller\n')
    net.addController('c0')

    info('*** Network Nodes\n')
    s1 = net.addSwitch('s1', cls=OVSSwitch)

    load_b = net.addDocker(
            'load_b', 
            ip='10.0.0.20', 
            dimage='projeto-load-balancer-load_balancer_nginx', 
            network_mode='none',
            dcmd="nginx -g 'daemon off;'")


    srv_a = net.addDocker(
            'srv_a', 
            ip='10.0.0.21', 
            dimage='projeto-load-balancer-server_a', 
            network_mode='none',
            dcmd="nginx -g 'daemon off;'")

    srv_b = net.addDocker(
            'srv_b', 
            ip='10.0.0.22', 
            dimage='projeto-load-balancer-server_b', 
            network_mode='none',
            dcmd="nginx -g 'daemon off;'")

    client = net.addDocker(
            'client', 
            ip = '10.0.0.10', 
            dimage='projeto-load-balancer-client',
            network_mode='none')


    info('*** Waiting for containters to start\n')
    sleep(5)

    info('*** Linking topology\n')
    net.addLink(srv_a, s1)
    net.addLink(srv_b, s1)
    net.addLink(client,s1)
    net.addLink(load_b,s1)

    info('*** Starting the network\n')
    net.start()

    info('*** Starting Mininet CLI\n')
    CLI(net)

    info('*** Stopping the network\n')
    net.stop()

# ababa

if __name__ == '__main__':
    setLogLevel('info')
    topology()
