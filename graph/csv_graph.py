import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import glob
import argparse

# Configuração do estilo dos gráficos
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

def load_csv_file(filepath):
    """Carrega arquivo CSV"""
    try:
        if filepath and os.path.exists(filepath):
            print(f"✓ Loading: {os.path.basename(filepath)}")
            df = pd.read_csv(filepath)
            if df.empty:
                print(f"⚠️  File is empty: {filepath}")
                return None
            return df
        else:
            if filepath:
                print(f"⚠️  File not found: {filepath}")
            return None
    except Exception as e:
        print(f"✗ Error loading {filepath}: {e}")
        return None

def resolve_file_path(file_arg):
    """Resolve caminho do arquivo, suportando padrões glob"""
    if not file_arg:
        return None
    
    if '*' in file_arg or '?' in file_arg:
        files = glob.glob(file_arg)
        if files:
            return files[0]
        else:
            print(f"⚠️  No files found matching pattern: {file_arg}")
            return None
    else:
        return file_arg if os.path.exists(file_arg) else None

def plot_cpu_metrics(df, server_name, output_file):
    """Gera gráficos para métricas de CPU"""
    if df is None or df.empty:
        print(f"⚠️  No data for {server_name} CPU metrics")
        return False
    
    try:
        # Converter timestamp para datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Gráfico 1: CPU Total
        axes[0].plot(df['datetime'], df['cpu_total_pct'], 
                     label='CPU Total', color='blue', linewidth=1.5)
        axes[0].set_title(f'{server_name} - CPU Total Usage (%)', fontsize=14, fontweight='bold')
        axes[0].set_ylabel('CPU Usage (%)')
        axes[0].set_xlabel('Time')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Destacar picos altos
        high_cpu = df[df['cpu_total_pct'] > 50]
        if not high_cpu.empty:
            axes[0].scatter(high_cpu['datetime'], high_cpu['cpu_total_pct'], 
                           color='red', s=30, alpha=0.6, label='High CPU (>50%)')
            axes[0].legend()
        
        # Gráfico 2: CPU User vs System
        axes[1].plot(df['datetime'], df['cpu_user_pct'], 
                     label='CPU User', color='green', linewidth=1.5, alpha=0.7)
        axes[1].plot(df['datetime'], df['cpu_sys_pct'], 
                     label='CPU System', color='orange', linewidth=1.5, alpha=0.7)
        axes[1].set_title(f'{server_name} - CPU User vs System Usage', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('CPU Usage (%)')
        axes[1].set_xlabel('Time')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Estatísticas descritivas
        print(f"\n=== {server_name} - CPU Statistics ===")
        print(f"Total CPU - Mean: {df['cpu_total_pct'].mean():.2f}%, Max: {df['cpu_total_pct'].max():.2f}%")
        print(f"User CPU - Mean: {df['cpu_user_pct'].mean():.2f}%, Max: {df['cpu_user_pct'].max():.2f}%")
        print(f"System CPU - Mean: {df['cpu_sys_pct'].mean():.2f}%, Max: {df['cpu_sys_pct'].max():.2f}%")
        
        return True
    except Exception as e:
        print(f"✗ Error generating CPU graph for {server_name}: {e}")
        return False

def plot_memory_metrics(df, server_name, output_file):
    """Gera gráficos para métricas de memória"""
    if df is None or df.empty:
        print(f"⚠️  No data for {server_name} memory metrics")
        return False
    
    try:
        # Converter timestamp para datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Converter bytes para MB
        df['anon_mb'] = df['anon_bytes'] / (1024 * 1024)
        df['file_mb'] = df['file_bytes'] / (1024 * 1024)
        df['sock_mb'] = df['sock_bytes'] / (1024 * 1024)
        df['total_mb'] = df['anon_mb'] + df['file_mb'] + df['sock_mb']
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Gráfico 1: Total Memory Usage
        axes[0].plot(df['datetime'], df['total_mb'], 
                     label='Total Memory', color='purple', linewidth=1.5)
        axes[0].fill_between(df['datetime'], df['total_mb'], alpha=0.3, color='purple')
        axes[0].set_title(f'{server_name} - Total Memory Usage', fontsize=14, fontweight='bold')
        axes[0].set_ylabel('Memory (MB)')
        axes[0].set_xlabel('Time')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Gráfico 2: Memory Breakdown
        axes[1].stackplot(df['datetime'], df['anon_mb'], df['file_mb'], df['sock_mb'],
                         labels=['Anonymous', 'File Cache', 'Socket'],
                         colors=['blue', 'green', 'orange'], alpha=0.7)
        axes[1].set_title(f'{server_name} - Memory Breakdown by Type', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('Memory (MB)')
        axes[1].set_xlabel('Time')
        axes[1].legend(loc='upper left')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Estatísticas descritivas
        print(f"\n=== {server_name} - Memory Statistics ===")
        print(f"Total Memory - Mean: {df['total_mb'].mean():.2f} MB, Max: {df['total_mb'].max():.2f} MB")
        print(f"Anonymous - Mean: {df['anon_mb'].mean():.2f} MB")
        print(f"File Cache - Mean: {df['file_mb'].mean():.2f} MB")
        print(f"Socket - Mean: {df['sock_mb'].mean():.2f} MB")
        
        return True
    except Exception as e:
        print(f"✗ Error generating Memory graph for {server_name}: {e}")
        return False

def plot_ping_metrics(df, target_ip, output_file):
    """Gera gráficos para métricas de ping"""
    if df is None or df.empty:
        print(f"⚠️  No data for ping to {target_ip}")
        return False
    
    try:
        # Converter timestamp para datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Gráfico 1: Ping Latency Over Time
        axes[0].plot(df['datetime'], df['avg_ms'], 
                     label='Average Latency', color='red', linewidth=1.5, marker='o', markersize=3)
        axes[0].set_title(f'Ping Latency to {target_ip}', fontsize=14, fontweight='bold')
        axes[0].set_ylabel('Latency (ms)')
        axes[0].set_xlabel('Time')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Destacar latências altas
        high_latency = df[df['avg_ms'] > 100]
        if not high_latency.empty:
            axes[0].scatter(high_latency['datetime'], high_latency['avg_ms'], 
                           color='red', s=50, alpha=0.7, label='High Latency (>100ms)')
            axes[0].legend()
        
        # Gráfico 2: Min, Avg, Max Latency
        axes[1].plot(df['datetime'], df['min_ms'], label='Min Latency', 
                     color='green', linewidth=1, alpha=0.7)
        axes[1].plot(df['datetime'], df['avg_ms'], label='Avg Latency', 
                     color='blue', linewidth=1.5, alpha=0.8)
        axes[1].plot(df['datetime'], df['max_ms'], label='Max Latency', 
                     color='red', linewidth=1, alpha=0.7)
        axes[1].set_title(f'Ping Latency Statistics to {target_ip}', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('Latency (ms)')
        axes[1].set_xlabel('Time')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Estatísticas descritivas
        print(f"\n=== Ping to {target_ip} - Statistics ===")
        print(f"Average Latency - Mean: {df['avg_ms'].mean():.2f} ms, Max: {df['avg_ms'].max():.2f} ms")
        print(f"Min Latency - Mean: {df['min_ms'].mean():.2f} ms")
        print(f"Max Latency - Mean: {df['max_ms'].mean():.2f} ms")
        
        return True
    except Exception as e:
        print(f"✗ Error generating Ping graph for {target_ip}: {e}")
        return False

def plot_delay_metrics(df, output_file):
    """Gera gráficos para métricas de delay"""
    if df is None or df.empty:
        print("⚠️  No data for delay metrics")
        return False
    
    try:
        # Converter timestamp para datetime
        df['datetime'] = pd.to_datetime(df['timestamp_ms'], unit='ms')
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Plot delay over time
        ax.plot(df['datetime'], df['delay_ms'], 
                label='Delay', color='red', linewidth=1.5, marker='s', markersize=4)
        ax.fill_between(df['datetime'], df['delay_ms'], alpha=0.3, color='red')
        ax.set_title('System Delay Over Time', fontsize=14, fontweight='bold')
        ax.set_ylabel('Delay (ms)')
        ax.set_xlabel('Time')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Destacar quando delay > 0
        delay_events = df[df['delay_ms'] > 0]
        if not delay_events.empty:
            ax.scatter(delay_events['datetime'], delay_events['delay_ms'], 
                      color='darkred', s=50, alpha=0.8, label='Delay Events')
            ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Estatísticas descritivas
        print(f"\n=== Delay Statistics ===")
        print(f"Average Delay: {df['delay_ms'].mean():.2f} ms")
        print(f"Max Delay: {df['delay_ms'].max():.2f} ms")
        print(f"Total delay events: {(df['delay_ms'] > 0).sum()}")
        
        return True
    except Exception as e:
        print(f"✗ Error generating Delay graph: {e}")
        return False

def plot_cpu_comparison(df_a, df_b, output_file):
    """Gera gráfico comparativo de CPU entre dois servidores"""
    if df_a is None or df_a.empty or df_b is None or df_b.empty:
        print("⚠️  Cannot generate CPU comparison: missing data for one or both servers")
        return False
    
    try:
        df_a['datetime'] = pd.to_datetime(df_a['timestamp'], unit='ms')
        df_b['datetime'] = pd.to_datetime(df_b['timestamp'], unit='ms')
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        ax.plot(df_a['datetime'], df_a['cpu_total_pct'], 
                label='Server A', color='blue', linewidth=1.5, alpha=0.8)
        ax.plot(df_b['datetime'], df_b['cpu_total_pct'], 
                label='Server B', color='red', linewidth=1.5, alpha=0.8)
        
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('CPU Usage (%)', fontsize=12)
        ax.set_title('CPU Total Usage Comparison: Server A vs Server B', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n=== CPU Comparison Statistics ===")
        print(f"Server A - Mean: {df_a['cpu_total_pct'].mean():.2f}%, Max: {df_a['cpu_total_pct'].max():.2f}%")
        print(f"Server B - Mean: {df_b['cpu_total_pct'].mean():.2f}%, Max: {df_b['cpu_total_pct'].max():.2f}%")
        
        return True
    except Exception as e:
        print(f"✗ Error generating CPU comparison graph: {e}")
        return False

def plot_memory_comparison(df_a, df_b, output_file):
    """Gera gráfico comparativo de memória entre dois servidores"""
    if df_a is None or df_a.empty or df_b is None or df_b.empty:
        print("⚠️  Cannot generate Memory comparison: missing data for one or both servers")
        return False
    
    try:
        df_a['datetime'] = pd.to_datetime(df_a['timestamp'], unit='ms')
        df_b['datetime'] = pd.to_datetime(df_b['timestamp'], unit='ms')
        
        df_a['total_mb'] = (df_a['anon_bytes'] + df_a['file_bytes'] + df_a['sock_bytes']) / (1024 * 1024)
        df_b['total_mb'] = (df_b['anon_bytes'] + df_b['file_bytes'] + df_b['sock_bytes']) / (1024 * 1024)
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        ax.plot(df_a['datetime'], df_a['total_mb'], 
                label='Server A', color='blue', linewidth=1.5, alpha=0.8)
        ax.plot(df_b['datetime'], df_b['total_mb'], 
                label='Server B', color='red', linewidth=1.5, alpha=0.8)
        
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Memory (MB)', fontsize=12)
        ax.set_title('Total Memory Usage Comparison: Server A vs Server B', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n=== Memory Comparison Statistics ===")
        print(f"Server A - Mean: {df_a['total_mb'].mean():.2f} MB, Max: {df_a['total_mb'].max():.2f} MB")
        print(f"Server B - Mean: {df_b['total_mb'].mean():.2f} MB, Max: {df_b['total_mb'].max():.2f} MB")
        
        return True
    except Exception as e:
        print(f"✗ Error generating Memory comparison graph: {e}")
        return False

def plot_ping_comparison(df_21, df_22, output_file):
    """Gera gráfico comparativo de ping entre dois destinos"""
    if df_21 is None or df_21.empty or df_22 is None or df_22.empty:
        print("⚠️  Cannot generate Ping comparison: missing data for one or both destinations")
        return False
    
    try:
        df_21['datetime'] = pd.to_datetime(df_21['timestamp'], unit='s')
        df_22['datetime'] = pd.to_datetime(df_22['timestamp'], unit='s')
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        ax.plot(df_21['datetime'], df_21['avg_ms'], 
                label='10.0.0.21', color='blue', linewidth=1.5, alpha=0.8)
        ax.plot(df_22['datetime'], df_22['avg_ms'], 
                label='10.0.0.22', color='red', linewidth=1.5, alpha=0.8)
        
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Latency (ms)', fontsize=12)
        ax.set_title('Ping Latency Comparison: 10.0.0.21 vs 10.0.0.22', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n=== Ping Comparison Statistics ===")
        print(f"10.0.0.21 - Mean: {df_21['avg_ms'].mean():.2f} ms, Max: {df_21['avg_ms'].max():.2f} ms")
        print(f"10.0.0.22 - Mean: {df_22['avg_ms'].mean():.2f} ms, Max: {df_22['avg_ms'].max():.2f} ms")
        
        return True
    except Exception as e:
        print(f"✗ Error generating Ping comparison graph: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Generate graphs from system metrics CSV files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate CPU graphs only
  python csv_graph.py --cpu-a /tmp/cpu_metrics_srv_a*.csv --cpu-b /tmp/cpu_metrics_srv_b*.csv
  
  # Generate Memory graphs only
  python csv_graph.py --memory-a /tmp/memory_metrics_srv_a*.csv --memory-b /tmp/memory_metrics_srv_b*.csv
  
  # Generate Ping graphs only
  python csv_graph.py --ping-21 /tmp/ping_10.0.0.21*.csv --ping-22 /tmp/ping_10.0.0.22*.csv
  
  # Generate everything with comparisons
  python csv_graph.py --cpu-a /tmp/cpu_metrics_srv_a*.csv --cpu-b /tmp/cpu_metrics_srv_b*.csv \\
                      --memory-a /tmp/memory_metrics_srv_a*.csv --memory-b /tmp/memory_metrics_srv_b*.csv \\
                      --ping-21 /tmp/ping_10.0.0.21*.csv --ping-22 /tmp/ping_10.0.0.22*.csv \\
                      --delay /tmp/delay_*.csv \\
                      --compare-cpu --compare-memory --compare-ping
        '''
    )
    
    # Arquivos de entrada
    parser.add_argument('--cpu-a', type=str, help='CPU metrics file for Server A (CSV)')
    parser.add_argument('--cpu-b', type=str, help='CPU metrics file for Server B (CSV)')
    parser.add_argument('--memory-a', type=str, help='Memory metrics file for Server A (CSV)')
    parser.add_argument('--memory-b', type=str, help='Memory metrics file for Server B (CSV)')
    parser.add_argument('--ping-21', type=str, help='Ping metrics file for 10.0.0.21 (CSV)')
    parser.add_argument('--ping-22', type=str, help='Ping metrics file for 10.0.0.22 (CSV)')
    parser.add_argument('--delay', type=str, help='Delay metrics file (CSV)')
    
    # Flags para gráficos comparativos
    parser.add_argument('--compare-cpu', action='store_true', help='Generate CPU comparison graph')
    parser.add_argument('--compare-memory', action='store_true', help='Generate Memory comparison graph')
    parser.add_argument('--compare-ping', action='store_true', help='Generate Ping comparison graph')
    
    # Output
    parser.add_argument('--output-dir', type=str, default='.', help='Output directory for graphs (default: current directory)')
    
    args = parser.parse_args()
    
    # Verificar se pelo menos um arquivo foi fornecido
    if not any([args.cpu_a, args.cpu_b, args.memory_a, args.memory_b, 
                args.ping_21, args.ping_22, args.delay]):
        parser.print_help()
        print("\n❌ Error: At least one input file must be provided")
        sys.exit(1)
    
    # Criar diretório de saída
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=" * 60)
    print("📊 Metrics Visualization Tool")
    print("=" * 60)
    
    # Carregar arquivos
    print("\n📂 Loading data files...")
    
    cpu_a_df = load_csv_file(resolve_file_path(args.cpu_a)) if args.cpu_a else None
    cpu_b_df = load_csv_file(resolve_file_path(args.cpu_b)) if args.cpu_b else None
    memory_a_df = load_csv_file(resolve_file_path(args.memory_a)) if args.memory_a else None
    memory_b_df = load_csv_file(resolve_file_path(args.memory_b)) if args.memory_b else None
    ping_21_df = load_csv_file(resolve_file_path(args.ping_21)) if args.ping_21 else None
    ping_22_df = load_csv_file(resolve_file_path(args.ping_22)) if args.ping_22 else None
    delay_df = load_csv_file(resolve_file_path(args.delay)) if args.delay else None
    
    print("\n" + "=" * 60)
    print("🎨 Generating graphs...")
    print("=" * 60)
    
    graphs_generated = 0
    
    # Gerar gráficos de CPU individuais
    if args.cpu_a:
        output_file = os.path.join(args.output_dir, 'cpu_metrics_server_a.png')
        if plot_cpu_metrics(cpu_a_df, 'Server A', output_file):
            graphs_generated += 1
    
    if args.cpu_b:
        output_file = os.path.join(args.output_dir, 'cpu_metrics_server_b.png')
        if plot_cpu_metrics(cpu_b_df, 'Server B', output_file):
            graphs_generated += 1
    
    # Gerar gráficos de memória individuais
    if args.memory_a:
        output_file = os.path.join(args.output_dir, 'memory_metrics_server_a.png')
        if plot_memory_metrics(memory_a_df, 'Server A', output_file):
            graphs_generated += 1
    
    if args.memory_b:
        output_file = os.path.join(args.output_dir, 'memory_metrics_server_b.png')
        if plot_memory_metrics(memory_b_df, 'Server B', output_file):
            graphs_generated += 1
    
    # Gerar gráficos de ping individuais
    if args.ping_21:
        output_file = os.path.join(args.output_dir, 'ping_metrics_10.0.0.21.png')
        if plot_ping_metrics(ping_21_df, '10.0.0.21', output_file):
            graphs_generated += 1
    
    if args.ping_22:
        output_file = os.path.join(args.output_dir, 'ping_metrics_10.0.0.22.png')
        if plot_ping_metrics(ping_22_df, '10.0.0.22', output_file):
            graphs_generated += 1
    
    # Gerar gráfico de delay
    if args.delay:
        output_file = os.path.join(args.output_dir, 'delay_metrics.png')
        if plot_delay_metrics(delay_df, output_file):
            graphs_generated += 1
    
    # Gerar gráficos comparativos (apenas se solicitado e dados disponíveis)
    if args.compare_cpu and args.cpu_a and args.cpu_b:
        output_file = os.path.join(args.output_dir, 'cpu_comparison.png')
        if plot_cpu_comparison(cpu_a_df, cpu_b_df, output_file):
            graphs_generated += 1
    
    if args.compare_memory and args.memory_a and args.memory_b:
        output_file = os.path.join(args.output_dir, 'memory_comparison.png')
        if plot_memory_comparison(memory_a_df, memory_b_df, output_file):
            graphs_generated += 1
    
    if args.compare_ping and args.ping_21 and args.ping_22:
        output_file = os.path.join(args.output_dir, 'ping_comparison.png')
        if plot_ping_comparison(ping_21_df, ping_22_df, output_file):
            graphs_generated += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Generated {graphs_generated} graph(s) successfully!")
    print(f"📁 Output directory: {args.output_dir}")
    print("=" * 60)
    
    if graphs_generated == 0:
        print("\n⚠️  No graphs were generated. Please check your input files.")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
