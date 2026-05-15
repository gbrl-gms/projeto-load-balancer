# Balanceamento de Carga Inteligente - Etapa 3

Este projeto faz parte da disciplina de Avaliação de Desempenho do IFPB. A Etapa 3 foca na consolidação da infraestrutura de rede heterogênea e no sistema de telemetria avançado, preparando o terreno para a implementação do agente de Inteligência Artificial no switch P4.

## 🏗️ Topologia e Componentes
A rede é emulada via **Containernet**, utilizando containers Docker para isolar os serviços em uma topologia em "Y":
- **Load Balancer (Nginx):** IP `10.0.0.20`. Responsável pela distribuição de tráfego inicial.
- **Application Servers (A e B):** IPs `10.0.0.21` e `10.0.0.22`. Executam o serviço web (porta 80), o servidor de testes `iperf3` e o agente de telemetria em Flask (porta 81).
- **Client:** Nó gerador de carga (IP `10.0.0.10`) responsável por simular requisições e coletar os estados da rede.

## 🚀 Como Rodar o Projeto

### 1. Pré-requisitos
- Docker e Docker Compose instalados.
- Kernel com suporte a Cgroups v2.

### 2. Subir, validar e confirmar limites da Infraestrutura
Na raiz do projeto, execute:
```bash
docker compose build --parallel

docker compose up -d containernet-lab

docker compose exec containernet-lab bash 
```

Dentro do containernet-lab:
```bash
service openvswitch-switch start
python3 nginx_lb.py # OU python3 bmv2_lb.py

# Inicia o serviço de switch virtual
service openvswitch-switch start

# Executa o script de monitoramento e coleta de dados
python3 nginx_lb.py
```

📊 Sistema de Telemetria
Nesta fase, o script nginx_lb.py utiliza a função get_state para realizar uma varredura constante dos servidores:

Latência (RTT): Cálculo do tempo de ida e volta entre cliente e servidor.

Throughput (Vazão): Medição da largura de banda disponível via Iperf3 em formato JSON.

Recursos de Sistema: Consumo real de CPU e Memória RAM obtidos via API REST (/metrics) rodando diretamente nos servidores.

🛠️ Tecnologias Utilizadas
Containernet / Mininet: Orquestração da rede SDN.

Docker: Virtualização dos nós de aplicação.

Nginx: Proxy reverso e balanceamento.

Python (Flask, Psutil): Agente de monitoramento e lógica de automação.

Iperf3: Diagnóstico de rede.


