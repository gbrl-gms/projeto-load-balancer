#!/usr/bin/env python3
import os
import argparse
from time import sleep
from mininet.net import Containernet
from mininet.node import Controller, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

# Caminho absoluto para a pasta de métricas/scripts
SCRIPTS_PATH = os.path.abspath('./metrics')

def parse_arguments():
    """Configura o argparse para receber o tempo de execução."""
    parser = argparse.ArgumentParser(description="Topologia Containernet com Load Balancer Nginx e Monitoramento.")
    parser.add_argument(
        '-t', '--time', 
        type=int, 
        default=60, 
        help='Tempo de execução do monitoramento em segundos (padrão: 60)'
    )
    return parser.parse_args()

def create_nodes(net):
    """Cria o switch e os nós Docker da topologia."""
    info('*** Adding Switch\n')
    s1 = net.addSwitch('s1', cls=OVSSwitch)

    info('*** Adding Docker Containers\n')
    
    # Balanceador Nginx
    load_b = net.addDocker(
        'load_b', 
        ip='10.0.0.20', 
        dimage='projeto-load-balancer-load_balancer_nginx', 
        network_mode='none',
        dcmd="nginx -g 'daemon off;'"
    )

    # Servidor A: Inicia o iperf, o monitor interno e o nginx
    srv_a = net.addDocker(
        'srv_a', 
        ip='10.0.0.21', 
        dimage='projeto-load-balancer-server_a',
        network_mode='none',
        dcmd="bash -c 'iperf3 -s -D && python3 /app/monitor.py & exec nginx -g \"daemon off;\"'",
        volumes=[f"{SCRIPTS_PATH}:/scripts", "/tmp:/tmp"]
    )

    # Servidor B
    srv_b = net.addDocker(
        'srv_b', 
        ip='10.0.0.22', 
        dimage='projeto-load-balancer-server_b',
        network_mode='none',
        dcmd="bash -c 'iperf3 -s -D && python3 /app/monitor.py & exec nginx -g \"daemon off;\"'",
        volumes=[f"{SCRIPTS_PATH}:/scripts", "/tmp:/tmp"]
    )

    # Cliente
    client = net.addDocker(
        'client', 
        ip='10.0.0.10', 
        dimage='projeto-load-balancer-client',
        network_mode='none',
        volumes=[f"{SCRIPTS_PATH}:/scripts", "/tmp:/tmp"]
    )

    return s1, load_b, srv_a, srv_b, client

def create_links(net, switch, nodes):
    """Cria as conexões (links) entre os nós e o switch."""
    info('*** Linking topology\n')
    for node in nodes:
        net.addLink(node, switch)

def run_monitoring_scripts(nodes_dict, duration):
    """Executa os scripts de monitoramento em background nos nós correspondentes."""
    info(f'*** Starting metrics collection for {duration} seconds...\n')
    
    srv_a = nodes_dict['srv_a']
    srv_b = nodes_dict['srv_b']
    client = nodes_dict['client']

    # 1. Executa o m-server.sh nos servidores (ajuste o caminho se /scripts/m-server.sh for diferente no container)
    srv_a.cmd(f"SRV=srv_a bash /scripts/m-server.sh {duration} &")
    srv_b.cmd(f"SRV=srv_b bash /scripts/m-server.sh {duration} &")

    # 2. Executa as duas instâncias do m-client.sh no cliente em background
    client.cmd(f"bash /scripts/m-client.sh {duration} 10.0.0.21 &")
    client.cmd(f"bash /scripts/m-client.sh {duration} 10.0.0.22 &")

    # 3. Executa a instância do vlc
    client.cmd(f"bash /scripts/m-dash.sh {duration} 10.0.0.20 80 /videos/video.mpd &")
    
    info('*** Monitoring scripts are running in background.\n')

def main():
    args = parse_arguments()
    duration = args.time

    net = Containernet(controller=Controller)

    info('*** Adding Controller\n')
    net.addController('c0')

    # Criação dos nós
    s1, load_b, srv_a, srv_b, client = create_nodes(net)

    # Criação dos links
    create_links(net, s1, [srv_a, srv_b, client, load_b])

    info('*** Starting the network\n')
    net.start()    

    # Execução dos scripts de métricas
    nodes_dict = {'srv_a': srv_a, 'srv_b': srv_b, 'client': client}
    run_monitoring_scripts(nodes_dict, duration)

    info('*** Starting Mininet CLI\n')
    CLI(net)

    info('*** Stopping the network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
