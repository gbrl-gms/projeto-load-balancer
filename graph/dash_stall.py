import re
import argparse
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    # Configuração do argparse para receber o arquivo de log por linha de comando
    parser = argparse.ArgumentParser(
        description="Analisa o log do VLC para medir a estagnação (Stall) do crescimento do buffer."
    )
    parser.add_argument(
        'log_file', 
        type=str, 
        help="Caminho para o arquivo de log do VLC (ex: test.log)"
    )
    
    args = parser.parse_args()
    log_file_path = args.log_file

    cached_times = []
    cached_pattern = re.compile(r'cached\.i_time\s*\((\d+)\)')

    # 1. Extração dos dados do log
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                match = cached_pattern.search(line)
                if match:
                    # Convertendo microssegundos para segundos
                    time_in_seconds = int(match.group(1)) / 1_000_000
                    cached_times.append(time_in_seconds)
                    
        if len(cached_times) < 2:
            print(f"Dados insuficientes em '{log_file_path}' para calcular taxas de crescimento.")
            return

        # 2. Cálculo das métricas de Estagnação (Stall)
        growth_rates = []  # Armazena o delta (quanto cresceu em segundos)
        stall_status = []  # 1 = Crescendo normalmente, 0 = Estagnado/Stall
        
        # O primeiro ponto serve de referência
        growth_rates.append(0)
        stall_status.append(1) 

        for i in range(1, len(cached_times)):
            delta = cached_times[i] - cached_times[i-1]
            growth_rates.append(delta)
            
            # Se delta for zero ou menor, o buffer DEIXOU de crescer (Stall)
            if delta <= 0:
                stall_status.append(0) # Estado de Engasgo/Estagnação
            else:
                stall_status.append(1) # Estado Saudável

        # Contagem de problemas encontrados
        total_stalls = stall_status.count(0)
        print(f"Análise concluída. Total de eventos de cache: {len(cached_times)}")
        print(f"Eventos onde o buffer DEIXOU de crescer (Stalls): {total_stalls}")

        # 3. Construção dos Gráficos
        sns.set_theme(style="whitegrid")
        fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

        # --- GRÁFICO TOP: Taxa de Crescimento (Delta) ---
        sns.lineplot(
            ax=axes[0], 
            x=range(len(growth_rates)), 
            y=growth_rates, 
            color='darkorange', 
            linewidth=2,
            marker='o',
            markersize=4
        )
        axes[0].set_title('Taxa de Crescimento do Cache (Variação em Segundos)', fontsize=14, fontweight='bold')
        axes[0].set_ylabel('Segundos Adicionados', fontsize=12)
        # Linha guia em zero para destacar visualmente onde parou de crescer
        axes[0].axhline(y=0, color='red', linestyle='--', alpha=0.7, label='Zero Crescimento')
        axes[0].legend()

        # --- GRÁFICO BOTTOM: Status de Stall (Binário) ---
        # Usamos drawstyle='steps-pre' para fazer o efeito de gráfico de degrau (Step Chart)
        axes[1].plot(
            range(len(stall_status)), 
            stall_status, 
            color='crimson', 
            linewidth=2.5, 
            drawstyle='steps-pre'
        )
        axes[1].fill_between(
            range(len(stall_status)), 
            stall_status, 
            step="pre", 
            alpha=0.15, 
            color='crimson'
        )
        axes[1].set_title('Gráfico de Stall (Estabilidade da Reprodução)', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Eventos de Cache (Sequência Temporal)', fontsize=12)
        axes[1].set_ylabel('Status (1=Ok, 0=Stall)', fontsize=12)
        axes[1].set_ylim(-0.2, 1.2)
        axes[1].set_yticks([0, 1])
        axes[1].set_yticklabels(['0 (TRAVADO)', '1 (CRESCENDO)'])

        plt.tight_layout()
        
        # Salva o resultado
        output_filename = 'analise_estagnacao_buffer.png'
        plt.savefig(output_filename)
        print(f"Gráficos gerados com sucesso e salvos como '{output_filename}'.")
        plt.show()

    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em: {log_file_path}")

if __name__ == '__main__':
    main()
