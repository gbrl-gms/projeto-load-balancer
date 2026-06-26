import re
import argparse
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    # Configuração do argparse para receber parâmetros da linha de comando
    parser = argparse.ArgumentParser(
        description="Extrai métricas de 'cached.i_time' de um log do VLC e gera um gráfico de linha."
    )
    # Define um argumento posicional obrigatório para o caminho do arquivo
    parser.add_argument(
        'log_file', 
        type=str, 
        help="Caminho para o arquivo de log do VLC (ex: test.log)"
    )
    
    # Processa os argumentos passados no terminal
    args = parser.parse_args()
    log_file_path = args.log_file

    # Lista para armazenar os valores convertidos de cache
    cached_times = []

    # Regex para capturar o número dentro dos parênteses após "cached.i_time"
    cached_pattern = re.compile(r'cached\.i_time\s*\((\d+)\)')

    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                match = cached_pattern.search(line)
                if match:
                    # Conversão de microssegundos para segundos
                    time_in_seconds = int(match.group(1)) / 1_000_000
                    cached_times.append(time_in_seconds)
                    
        if not cached_times:
            print(f"Nenhum dado de 'cached.i_time' foi encontrado no arquivo '{log_file_path}'.")
            return
            
        print(f"{len(cached_times)} registros de cache encontrados. Gerando gráfico...")

        # Configuração do tema visual
        sns.set_theme(style="whitegrid")

        plt.figure(figsize=(12, 6))
        
        # Gerando o gráfico de linha baseado na sequência temporal dos eventos
        sns.lineplot(x=range(len(cached_times)), y=cached_times, color='royalblue', linewidth=2)

        # Customização de títulos e legendas
        plt.title('VLC Cached Time Over Time (Tempo de Cache)', fontsize=16, fontweight='bold')
        plt.xlabel('Eventos de Cache (Sequência Temporal)', fontsize=12)
        plt.ylabel('Tempo em Cache (Segundos)', fontsize=12)
        
        # Altera o limite do eixo Y para o teto de 600 segundos
        plt.ylim(0, 600) 

        plt.tight_layout()
        
        # Salva o gráfico
        plt.savefig('vlc_cached_time_graph.png')
        print("Gráfico gerado com sucesso e salvo como 'vlc_cached_time_graph.png'.")
        plt.show()

    except FileNotFoundError:
        print(f"Erro: O arquivo de log não foi encontrado no caminho especificado: {log_file_path}")

if __name__ == '__main__':
    main()
