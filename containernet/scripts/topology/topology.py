#!/usr/bin/env python3
import os
import argparse
from time import sleep
from mininet.net import Containernet
from mininet.node import Controller, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def create_nodes(net):
    nodes_dict = {}

    info('*** Adding Network Nodes (Switches and Docker Containers)\n')
    
    nodes_dict['s1'] = net.addSwitch('s1', cls=OVSSwitch)
    nodes_dict['s2'] = net.addSwitch('s2', cls=OVSSwitch)
    nodes_dict['s3'] = net.addSwitch('s3', cls=OVSSwitch)
    nodes_dict['h1'] = net.addDocker('h1', dimage='inetrm-client', ip='10.0.0.1', network_mode='none', volumes=["/tmp:/tmp"])
    nodes_dict['h2'] = net.addDocker('h2', dimage='inetrm-client', ip='10.0.0.2', network_mode='none', volumes=["/tmp:/tmp"])
    nodes_dict['h3'] = net.addDocker('h3', dimage='inetrm-client', ip='10.0.0.3', network_mode='none', volumes=["/tmp:/tmp"])
    nodes_dict['h4'] = net.addDocker('h4', dimage='inetrm-client', ip='10.0.0.4', network_mode='none', volumes=["/tmp:/tmp"])
    nodes_dict['h5'] = net.addDocker('h5', dimage='inetrm-server', ip='10.0.0.5', network_mode='none', volumes=["/tmp:/tmp"])
    nodes_dict['h6'] = net.addDocker('h6', dimage='inetrm-server', ip='10.0.0.6', network_mode='none', volumes=["/tmp:/tmp"])

    return nodes_dict

def create_links(net, nodes_dict):
    info('*** Linking topology\n')
    net.addLink(nodes_dict['s1'], nodes_dict['s2'])
    net.addLink(nodes_dict['s2'], nodes_dict['s3'])
    net.addLink(nodes_dict['s1'], nodes_dict['s3'])
    net.addLink(nodes_dict['s1'], nodes_dict['h1'])
    net.addLink(nodes_dict['s1'], nodes_dict['h2'])
    net.addLink(nodes_dict['s2'], nodes_dict['h3'])
    net.addLink(nodes_dict['s2'], nodes_dict['h4'])
    net.addLink(nodes_dict['s3'], nodes_dict['h5'])
    net.addLink(nodes_dict['s3'], nodes_dict['h6'])

def run_monitoring_scripts(nodes_dict, duration):
    ...

def parse_arguments():
    parser = argparse.ArgumentParser(description="Containernet Topology")
    parser.add_argument('--time', type=int, default=60, help="Duration of monitoring")
    return parser.parse_args()

def main():
    args = parse_arguments()
    duration = args.time

    net = Containernet(controller=Controller)

    info('*** Adding Controller\n')
    net.addController('c0')

    nodes_dict = create_nodes(net)
    
    create_links(net, nodes_dict)

    info('*** Starting the network\n')
    net.start()    

    # run_monitoring_scripts(nodes_dict, duration)

    info('*** Starting Mininet CLI\n')
    CLI(net)

    info('*** Stopping the network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()