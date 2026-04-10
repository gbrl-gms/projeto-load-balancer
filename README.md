# Balanceamento de Carga Inteligente com Q-Learning (Etapa 2)

Este projeto faz parte da disciplina de Avaliação de Desempenho do IFPB. O objetivo é desenvolver um balanceador de carga dinâmico que utiliza Aprendizado por Reforço (Q-Learning) em um switch programável P4 para otimizar a distribuição de tráfego em um ambiente heterogêneo.

## 🏗️ Topologia do Ambiente
A rede foi construída utilizando **Docker Compose** seguindo uma topologia em **Y**:
- **1 Nó Cliente:** Responsável por gerar requisições HTTP e coletar métricas de tempo de resposta.
- **1 Switch Central (BMv2/P4):** Atua como o Agente de IA que intercepta e redireciona pacotes.
- **2 Servidores de Aplicação (A e B):** Containers Flask que expõem telemetria de Sistema Operacional (CPU e Memória).

## 🚀 Como Rodar o Projeto

### 1. Pré-requisitos
- Docker e Docker Compose instalados.
- Kernel com suporte a Cgroups v2.

### 2. Subir, validar e confirmar limites da Infraestrutura
Na raiz do projeto, execute:
```bash
sudo docker-compose up -d --build

sudo docker update --cpus 0.8 servidor_a

sudo docker update --cpus 0.2 servidor_b

sudo docker ps

sudo docker inspect servidor_a | grep NanoCpus

sudo docker inspect servidor_b | grep NanoCpus
