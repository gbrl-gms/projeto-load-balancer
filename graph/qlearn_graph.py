import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

def main():
    # 1. Configura o argparse para gerenciar os argumentos de linha de comando
    parser = argparse.ArgumentParser(
        description="Script para plotar e comparar latências de servidores a partir de um log CSV."
    )
    
    # Define o argumento obrigatório para o caminho do arquivo
    parser.add_argument(
        'csv_path', 
        type=str, 
        help="Caminho para o arquivo CSV contendo os dados do experimento."
    )
    
    # Processa os argumentos
    args = parser.parse_args()
    
    # 2. Verifica se o arquivo realmente existe
    if not os.path.exists(args.csv_path):
        print(f"❌ Erro: O arquivo '{args.csv_path}' não foi encontrado.")
        return
        
    try:
        # 3. Carrega os dados usando pandas
        df = pd.read_csv(args.csv_path)
        
        # Remove espaços em branco extras dos nomes das colunas (se houver)
        df.columns = df.columns.str.strip()
        
        # 4. Calcula a Média Ponderada da Latência
        numerator = (df['lat_a'] * df['weight_a']) + (df['lat_b'] * df['weight_b'])
        denominator = df['weight_a'] + df['weight_b']
        df['media_ponderada'] = numerator / denominator
        
        # 5. Configura e plota o gráfico
        plt.figure(figsize=(12, 6))
        
        plt.plot(df['iteration'], df['lat_a'], label='Latência A (ms)', color='#1f77b4', alpha=0.6, linewidth=1.5)
        plt.plot(df['iteration'], df['lat_b'], label='Latência B (ms)', color='#ff7f0e', alpha=0.6, linewidth=1.5)
        plt.plot(df['iteration'], df['media_ponderada'], label='Média Ponderada (ms)', color='#2ca02c', linewidth=2.5, linestyle='--')
        
        # Customização do Gráfico
        plt.title('Análise de Latência: Servidor A vs Servidor B vs Média Ponderada', fontsize=14, fontweight='bold', pad=15)
        plt.xlabel('Iteração', fontsize=12)
        plt.ylabel('Latência (ms)', fontsize=12)
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.legend(fontsize=11, loc='upper right')
        
        # Otimiza o espaçamento
        plt.tight_layout()

        # Define o nome do arquivo de saída
        output_image = "analise_latencia.png"

        # Salva o gráfico no disco
        plt.savefig(output_image, dpi=300)
        print(f"💾 Gráfico salvo com sucesso em: {output_image}")

        # Opcional: Fecha a figura para liberar memória
        plt.close()
        
    except Exception as e:
        print(f"❌ Ocorreu um erro ao processar o arquivo: {e}")

if __name__ == "__main__":
    main()
