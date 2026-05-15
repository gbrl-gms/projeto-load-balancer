from mininet.net import Containernet
from mininet.node import Controller, Docker, OVSSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from time import sleep
import json

def get_state(net, target_ip):
    client = net.get('client')

    # 1. Latência: adicionado tratamento para caso o comando ping retorne vazio
    res_ping = client.cmd(f'ping -c 1 -W 1 {target_ip} | grep rtt | cut -d"/" -f5')
    try:
        latency = float(res_ping) if res_ping.strip() else 999.0
    except:
        latency = 999.0

    # 2. Throughput (Vazão)
    res_iperf = client.cmd(f'iperf3 -c {target_ip} -t 1 -p 80 -J')
    try:
        data = json.loads(res_iperf)
        throughput = data['end']['sum_received']['bits_per_second'] / 1e6  # Mbps
    except:
        throughput = 0.0

    # 3. CPU e Memória (Métricas de sistema via API Flask na porta 81)
    res_so = client.cmd(f'curl -s --max-time 2 http://{target_ip}:81/metrics')
    try:
        so_data = json.loads(res_so)
        cpu = so_data['cpu']
        mem = so_data['memory']
    except:
        # Se o curl falhar, mantém os valores de segurança
        cpu, mem = 100.0, 100.0 

    return {"lat": latency, "thr": throughput, "cpu": cpu, "mem": mem}

def topology():
    net = Containernet(controller=Controller)

    info('*** Adding Controller\n')
    net.addController('c0')

    info('*** Network Nodes\n')
    s1 = net.addSwitch('s1', cls=OVSSwitch)

    # Balanceador Nginx
    load_b = net.addDocker(
        'load_b', 
        ip='10.0.0.20', 
        dimage='projeto-load-balancer-load_balancer_nginx', 
        network_mode='none',
        dcmd="nginx -g 'daemon off;'"
    )

    # Servidor A: Inicia o iperf, o monitor de recursos e o nginx
    srv_a = net.addDocker(
        'srv_a', 
        ip='10.0.0.21', 
        dimage='projeto-load-balancer-server_a', 
        network_mode='none',
        dcmd="iperf3 -s -D; python3 /app/monitor.py & nginx -g 'daemon off;'"
    )

    # Servidor B
    srv_b = net.addDocker(
        'srv_b', 
        ip='10.0.0.22', 
        dimage='projeto-load-balancer-server_b', 
        network_mode='none',
        dcmd="iperf3 -s -D; python3 /app/monitor.py & nginx -g 'daemon off;'"
    )

    client = net.addDocker(
        'client', 
        ip = '10.0.0.10', 
        dimage='projeto-load-balancer-client',
        network_mode='none'
    )

    info('*** Linking topology\n')
    net.addLink(srv_a, s1)
    net.addLink(srv_b, s1)
    net.addLink(client, s1)
    net.addLink(load_b, s1)

    info('*** Starting the network\n')
    net.start()    

    info('*** Waiting for containers to start (15s)\n')
    sleep(15) # Aumentado um pouco para garantir que o Flask suba

    info('*** Baseline Collection Started (Press Ctrl+C for CLI)\n')
    try:
        while True:
            # Coleta métricas de ambos os servidores
            state_a = get_state(net, '10.0.0.21')
            state_b = get_state(net, '10.0.0.22')

            # Exibição dos dados coletados
            print("-" * 50)
            print(f"[SRV_A] CPU: {state_a['cpu']}% | MEM: {state_a['mem']}% | LAT: {state_a['lat']}ms | THR: {state_a['thr']}Mbps")
            print(f"[SRV_B] CPU: {state_b['cpu']}% | MEM: {state_b['mem']}% | LAT: {state_b['lat']}ms | THR: {state_b['thr']}Mbps")
            
            sleep(5)
            
    except KeyboardInterrupt:
        info('\n*** Exiting collection loop and heading to CLI\n')

    info('*** Starting Mininet CLI\n')
    CLI(net)

    info('*** Stopping the network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()
