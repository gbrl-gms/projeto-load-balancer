import numpy as np
import random
import time
import csv
import signal
import sys
import subprocess

# ==============================================================================
# CONFIGURAÇÕES E HIPERPARÂMETROS DO EXPERIMENTO
# ==============================================================================
NUM_STATES = (8, 8)
NUM_ACTIONS = 3
ALPHA = 0.1
GAMMA = 0.9

INITIAL_EPSILON = 1.0
MIN_EPSILON = 0.05
STEPS_TO_MIN = 240
LINEAR_DECAY = (INITIAL_EPSILON - MIN_EPSILON) / STEPS_TO_MIN

POSSIBLE_WEIGHTS = [1, 2, 3, 5, 8, 12, 15]
CSV_FILE_PATH = "/tmp/qlearn.csv"
LATENCY_FILE_PATH = "/tmp/upstream_latency"
NGINX_CONF_PATH = "/etc/nginx/nginx.conf"

# ==============================================================================
# 1. MÓDULO DO AMBIENTE (SIMULAÇÃO / INFRAESTRUTURA)
# ==============================================================================
def get_upstream_latency(weight_a, weight_b):
    """
    Lê as latências brutas geradas pelo script externo a partir do arquivo /tmp/upstream_latency.
    Os parâmetros weight_a e weight_b foram mantidos para não quebrar a assinatura da função,
    embora a latência agora venha diretamente do arquivo de teste.
    """
    try:
        with open(LATENCY_FILE_PATH, "r") as f:
            lines = f.readlines()
            
        # Converte a primeira linha para a latência A e a segunda para a latência B
        lat_a = float(lines[0].strip())
        lat_b = float(lines[1].strip())
        
        # Garante que não teremos latências negativas que possam quebrar a discretização
        return max(0.0, lat_a), max(0.0, lat_b)
        
    except (FileNotFoundError, IndexError, ValueError):
        # Caso o arquivo não exista (ainda não foi criado), esteja incompleto ou sendo escrito:
        # Retorna um valor padrão de segurança (ex: 100ms) para que o loop continue rodando
        default_latency_a = 100.0
        default_latency_b = 100.0
        return default_latency_a, default_latency_b

def discretize_latency(latency):
    """Mapeia a latência contínua para um índice de estado discreto (0 a 7)."""
    if latency < 0: 
        return 0
    state = int(latency // 50)
    return state if state < 8 else 7

def get_current_state(lat_a, lat_b):
    """Retorna a tupla de estados correspondente às latências atuais."""
    return (discretize_latency(lat_a), discretize_latency(lat_b))

# ==============================================================================
# 2. MÓDULO DO AGENTE Q-LEARNING
# ==============================================================================
def choose_action(q_table, state, epsilon):
    """Seleciona uma ação usando a estratégia Epsilon-Greedy."""
    if random.uniform(0, 1) < epsilon:
        return random.randint(0, NUM_ACTIONS - 1)  # Exploração
    return np.argmax(q_table[state])                # Explotação

def update_weight_indices(idx_a, idx_b, action):
    """Calcula os novos índices na lista de pesos com base na ação tomada."""
    if action == 0 and idx_a < len(POSSIBLE_WEIGHTS) - 1:
        idx_a += 1
        if idx_b > 0: idx_b -= 1
    elif action == 1 and idx_a > 0:
        idx_a -= 1
        if idx_b < len(POSSIBLE_WEIGHTS) - 1: idx_b += 1
    return idx_a, idx_b

def calculate_reward(lat_a, lat_b, weight_a, weight_b):
    """Mapeia o desempenho do sistema em um valor de recompensa numérica."""
    return 100 - ((lat_a * weight_a) + (lat_b * weight_b))/(weight_a + weight_b)

def train_agent(q_table, state, action, reward, next_state):
    """Aplica a Equação de Bellman para atualizar o conhecimento da Q-Table."""
    old_q = q_table[state][action]
    max_future = np.max(q_table[next_state])
    q_table[state][action] = old_q + ALPHA * (reward + GAMMA * max_future - old_q)

def update_epsilon(epsilon):
    """Aplica o decaimento linear ao valor do Epsilon até o limite mínimo."""
    if epsilon > MIN_EPSILON:
        epsilon -= LINEAR_DECAY
        if epsilon < MIN_EPSILON:
            epsilon = MIN_EPSILON
    return epsilon

def apply_weights(weight_a, weight_b):
    """
    Escreve os novos pesos descobertos pelo Q-Learning no arquivo de upstream
    do Nginx e dispara um reload leve no serviço.
    """
    # 1. Define o bloco upstream com a sintaxe oficial do Nginx
    # Substitua '192.168.1.10' e '192.168.1.11' pelos IPs reais dos seus servidores de teste
    nginx_config = f"""
worker_processes auto;

events {{
    worker_connections 1024;
}}

http {{
    include       mime.types;
    default_type  application/octet-stream;

    # 1. Definindo o formato de log customizado com as métricas de latência
    log_format proxy_latency '$remote_addr - $remote_user [$time_local] '
                             '"$request" $status $body_bytes_sent '
                             '"$http_referer" "$http_user_agent" '
                             'rt=$request_time uct="$upstream_connect_time" '
                             'uht="$upstream_header_time" urt="$upstream_response_time"';

    upstream servidores_backend {{
        server 10.0.0.21:80 weight={weight_a};
        server 10.0.0.22:80 weight={weight_b};
    }}

    server {{
        listen 80;
        server_name balanceador_baseline;

        # 2. Ativando o log de acessos usando o formato 'proxy_latency' que criamos acima
        access_log /var/log/nginx/access.log proxy_latency;

        location / {{
            proxy_pass http://servidores_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

            # Timeouts para evitar que o balanceador trave se um backend demorar
            proxy_connect_timeout 5s;
            proxy_read_timeout 10s;
        }}

        # Status para monitoramento do próprio balanceador
        location /nginx_status {{
            stub_status;
            allow all;
        }}
    }}
}}
    """

    try:
        # 2. Sobrescreve o arquivo de configuração do upstream
        with open(NGINX_CONF_PATH, "w") as f:
            f.write(nginx_config)

        # 3. Executa o reload no Nginx via linha de comando
        # O parâmetro '-s reload' faz o Nginx ler a nova config sem derrubar o proxy
        subprocess.run(["nginx", "-s", "reload"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    except Exception as e:
        # Evita que o script de testes caia caso haja um erro de permissão (ex: esquecer o sudo)
        print(f"[Aviso Infra] Falha ao aplicar pesos no Nginx: {e}")

# ==============================================================================
# 3. MÓDULO DE TELEMETRIA E IO (SINAIS E CSV)
# ==============================================================================
def initialize_csv(file_name):
    """Abre o arquivo CSV e escreve o cabeçalho das métricas."""
    opened_file = open(file_name, mode='w', newline='', encoding='utf-8')
    writer = csv.writer(opened_file)
    writer.writerow([
        "iteration", "lat_a", "lat_b", "weight_a", "weight_b", "cumulative_reward", "epsilon"
    ])
    opened_file.flush()
    return opened_file, writer

def log_metrics(writer, opened_file, iteration, lat_a, lat_b, w_a, w_b, cum_reward, epsilon):
    """Salva os dados da iteração atual no disco rígido de forma síncrona."""
    writer.writerow([
        iteration, round(lat_a, 2), round(lat_b, 2), w_a, w_b, round(cum_reward, 2), round(epsilon, 4)
    ])
    opened_file.flush()

def setup_signal_handler(csv_file_handle):
    """Define o comportamento do script ao receber interrupções do sistema."""
    def terminate_experiment(signum, frame):
        print(f"\n[SIGNAL {signum}] Closing CSV file safely...")
        csv_file_handle.close()
        print(f"Data saved successfully to: {CSV_FILE_PATH}")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, terminate_experiment)
    signal.signal(signal.SIGTERM, terminate_experiment)

# ==============================================================================
# INTERFACE PRINCIPAL DE EXECUÇÃO
# ==============================================================================
def run_experiment():
    # Inicializações globais do loop
    q_table = np.zeros(NUM_STATES + (NUM_ACTIONS,))
    idx_a, idx_b = 3, 3
    epsilon = INITIAL_EPSILON
    iteration = 0
    cumulative_reward = 0.0

    # Configuração dos arquivos e segurança
    opened_file, writer = initialize_csv(CSV_FILE_PATH)
    setup_signal_handler(opened_file)

    print(f"🔬 Modularized experiment running. Saving metrics to '{CSV_FILE_PATH}'...")
    print("Epsilon will reach its minimum value in 60 seconds. Press Ctrl+C to terminate.\n")

    try:
        while True:
            start_time = time.time()
            iteration += 1
            
            # Passo 1: Observação do ambiente atual
            weight_a, weight_b = POSSIBLE_WEIGHTS[idx_a], POSSIBLE_WEIGHTS[idx_b]
            lat_a, lat_b = get_upstream_latency(weight_a, weight_b)
            current_state = get_current_state(lat_a, lat_b)
            
            # Passo 2: Decisão da Ação (Epsilon-Greedy)
            action = choose_action(q_table, current_state, epsilon)
            
            # Passo 3: Execução da Ação (Transição de pesos)
            idx_a, idx_b = update_weight_indices(idx_a, idx_b, action)
            new_weight_a, new_weight_b = POSSIBLE_WEIGHTS[idx_a], POSSIBLE_WEIGHTS[idx_b]
            apply_weights(new_weight_a, new_weight_b)
            
            # Passo 4: Coleta de consequências imediatas do novo estado
            next_lat_a, next_lat_b = get_upstream_latency(new_weight_a, new_weight_b)
            next_state = get_current_state(next_lat_a, next_lat_b)
            
            reward = calculate_reward(next_lat_a, next_lat_b, new_weight_a, new_weight_b)
            cumulative_reward += reward
            
            # Passo 5: Atualização da Inteligência e Decaimento
            train_agent(q_table, current_state, action, reward, next_state)
            epsilon = update_epsilon(epsilon)
            
            # Passo 6: Persistência dos Dados de Pesquisa
            log_metrics(writer, opened_file, iteration, next_lat_a, next_lat_b, new_weight_a, new_weight_b, cumulative_reward, epsilon)
            
            # Sincronização temporal estrita do passo (1 segundo por ciclo)
            elapsed_time = time.time() - start_time
            time.sleep(max(0, 1.0 - elapsed_time))

    except Exception as e:
        print(f"A critical error occurred during execution: {e}")
        opened_file.close()

if __name__ == "__main__":
    run_experiment()
