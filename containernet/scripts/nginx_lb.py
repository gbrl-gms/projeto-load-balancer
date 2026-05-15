from mininet.net import Containernet
from mininet.node import Controller, Docker, OVSSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from time import sleep
import json

def coletar_estado(net, ip_alvo):
    client = net.get('client')

    # 1. latencia (do clineten pro servidor)
    res_ping = client.cmd(f'ping -c 1 -W 1 {ip_alvo} | grep rtt | cut -d"/" -f5')
    try:
        latencia = float(res_ping)
    except:
        latencia = 999.0

    # 2. throughput
    res_iperf = client.cmd(f'iperf3 -c {ip_alvo} -t 1 -p 80 -J')
    try:
        data = json.loads(res_iperf)
        vazao = data['end']['sum_received']['bits_per_second'] / 1e6  # Convertendo para Mbps
    except:
        vazao = 0.0

    # 3. cpu e memoria (o cliente so fa zum curl na porta 81 do servidor alvo)
    res_so = client.cmd(f'curl -s http://{ip_alvo}:81/metrics')
    try:
                so_data = json.loads(res_so)
                cpu = so_data['cpu']
                mem = so_data['memory']
        except:
        cpu, mem = 100.0, 100.0 # valor de segurança

        return {"lat": latencia, "thr": vazao, "cpu": cpu, "mem": mem}

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

    info('*** Linking topology\n')
    net.addLink(srv_a, s1)
    net.addLink(srv_b, s1)
    net.addLink(client,s1)
    net.addLink(load_b,s1)

    info('*** Starting the network\n')
    net.start()    

    info('*** Waiting for containters to start\n')
    sleep(10)

    s1 = net.addSwitch('s1', cls=OVSSwitch)
    load_b = net.addDocker('load_b', ip='10.0.0.20', dimage='projeto-load-balancer-load_balancer_nginx', network_mode='none')
    srv_a = net.addDocker('srv_a', ip='10.0.0.21', dimage='projeto-load-balancer-server_a', network_mode='none')
    srv_b = net.addDocker('srv_b', ip='10.0.0.22', dimage='projeto-load-balancer-server_b', network_mode='none')
    client = net.addDocker('client', ip='10.0.0.10', dimage='projeto-load-balancer-client', network_mode='none')


    info('*** Aguardando inicialização dos serviços (10s)\n')
    sleep(10)

    info('*** Coleta de Baseline Iniciada (Pressione Ctrl+C para o CLI)\n')
    try:
        while True:
            # Coleta do servidor A e B
            estado_a = coletar_estado(net, '10.0.0.21')
            estado_b = coletar_estado(net, '10.0.0.22')

            # Prints organizados para o log
            print("-" * 50)
            print(f"[SRV_A] CPU: {estado_a['cpu']}% | MEM: {estado_a['mem']}% | LAT: {estado_a['lat']}ms | THR: {estado_a['thr']}Mbps")
            print(f"[SRV_B] CPU: {estado_b['cpu']}% | MEM: {estado_b['mem']}% | LAT: {estado_b['lat']}ms | THR: {estado_b['thr']}Mbps")
            
            # Aqui no futuro entra o Q-learning pra decidir pra onde mandar o cliente, mas por enquanto so coletamos os dados e printamos
            sleep(5)
            
    except KeyboardInterrupt:
        info('\n*** Saindo do loop de coleta e indo para o CLI\n')

    info('*** Starting Mininet CLI\n')
    CLI(net)

    info('*** Stopping the network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()
