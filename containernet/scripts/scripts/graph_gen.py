import re
import matplotlib.pyplot as plt
import seaborn as sns

log_file_path = 'dash_buffer_20260612_004509.log'

# Lista para armazenar os valores do buffer
buffer_levels = []

# Regex para procurar a palavra "buffering" (ignorando maiúsculas/minúsculas) 
# seguida por espaços e um número com o símbolo '%'
# O (\d+) "captura" apenas a parte numérica.
buffer_pattern = re.compile(r'(?i)buffering\s+(\d+)%')

try:
    with open(log_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            match = buffer_pattern.search(line)
            if match:
                buffer_levels.append(int(match.group(1)))
                
    if not buffer_levels:
        print("No buffering data was found. Check if the log pattern matches the Regex.")
    else:
        print(f"{len(buffer_levels)} buffering records found. Generating graph...")

        sns.set_theme(style="whitegrid")

        plt.figure(figsize=(12, 6))
        
        sns.lineplot(x=range(len(buffer_levels)), y=buffer_levels, color='royalblue', linewidth=2)

        plt.title('Video Buffer Levels (VCL) overtime', fontsize=16, fontweight='bold')
        plt.xlabel('Buffering Events (Temporal sequence)', fontsize=12)
        plt.ylabel('Buffer (%)', fontsize=12)
        
        plt.ylim(0, 105) 

        plt.tight_layout()
        plt.savefig('buffer_graph.png', dpi=300)
        print("Graph saved as 'buffer_graph.png'.")

except FileNotFoundError:
    print(f"Error: The file '{log_file_path}' was not found. Please check the path.")