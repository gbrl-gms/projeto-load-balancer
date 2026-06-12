import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import pandas as pd
import os
import glob
import argparse

# Configuração dos gráficos
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

def load_iperf_json(filepath):
    """Carrega e parseia o arquivo JSON do iperf3"""
    try:
        if filepath and os.path.exists(filepath):
            print(f"✓ Loading: {os.path.basename(filepath)}")
            with open(filepath, 'r') as f:
                data = json.load(f)
            return data
        else:
            print(f"⚠️  File not found: {filepath}")
            return None
    except Exception as e:
        print(f"✗ Error loading {filepath}: {e}")
        return None

def extract_interval_data(data, target_ip):
    """Extrai dados dos intervalos de 1 segundo"""
    intervals = []
    
    if not data or 'intervals' not in data:
        return intervals
    
    for interval in data['intervals']:
        if 'sum' in interval:
            interval_data = {
                'timestamp': interval['sum']['start'],
                'end_time': interval['sum']['end'],
                'bits_per_second': interval['sum']['bits_per_second'] / 1e9,  # Convert to Gbps
                'bytes': interval['sum']['bytes'] / (1024**3),  # Convert to GB
                'retransmits': interval['sum']['retransmits'],
                'target_ip': target_ip
            }
            
            # Extrair dados adicionais do stream (se disponível)
            if 'streams' in interval and len(interval['streams']) > 0:
                stream = interval['streams'][0]
                interval_data['rtt'] = stream.get('rtt', 0)
                interval_data['rttvar'] = stream.get('rttvar', 0)
                interval_data['snd_cwnd'] = stream.get('snd_cwnd', 0)
            
            intervals.append(interval_data)
    
    return intervals

def plot_throughput_comparison(data_21, data_22, output_file):
    """Gráfico comparativo de throughput (banda)"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plotar throughput para ambos os destinos
    if data_21:
        times_21 = [d['end_time'] for d in data_21]
        throughput_21 = [d['bits_per_second'] for d in data_21]
        ax.plot(times_21, throughput_21, label='10.0.0.21', 
                color='blue', linewidth=1.5, alpha=0.8)
    
    if data_22:
        times_22 = [d['end_time'] for d in data_22]
        throughput_22 = [d['bits_per_second'] for d in data_22]
        ax.plot(times_22, throughput_22, label='10.0.0.22', 
                color='red', linewidth=1.5, alpha=0.8)
    
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('Throughput (Gbps)', fontsize=12)
    ax.set_title('iPerf3 Throughput Comparison: 10.0.0.21 vs 10.0.0.22', 
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    # Adicionar estatísticas
    stats_text = ""
    if data_21:
        avg_21 = np.mean([d['bits_per_second'] for d in data_21])
        max_21 = max([d['bits_per_second'] for d in data_21])
        stats_text += f"10.0.0.21 - Avg: {avg_21:.2f} Gbps, Max: {max_21:.2f} Gbps\n"
    
    if data_22:
        avg_22 = np.mean([d['bits_per_second'] for d in data_22])
        max_22 = max([d['bits_per_second'] for d in data_22])
        stats_text += f"10.0.0.22 - Avg: {avg_22:.2f} Gbps, Max: {max_22:.2f} Gbps"
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated: {output_file}")

def plot_rtt_analysis(data_21, data_22, output_file):
    """Gráfico de análise de RTT (Round Trip Time)"""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # RTT over time
    if data_21:
        rtt_data_21 = [(d['end_time'], d.get('rtt', 0)) for d in data_21 if d.get('rtt', 0) > 0]
        if rtt_data_21:
            times_21, rtt_21 = zip(*rtt_data_21)
            axes[0].plot(times_21, rtt_21, label='10.0.0.21', 
                        color='blue', linewidth=1, alpha=0.7)
    
    if data_22:
        rtt_data_22 = [(d['end_time'], d.get('rtt', 0)) for d in data_22 if d.get('rtt', 0) > 0]
        if rtt_data_22:
            times_22, rtt_22 = zip(*rtt_data_22)
            axes[0].plot(times_22, rtt_22, label='10.0.0.22', 
                        color='red', linewidth=1, alpha=0.7)
    
    axes[0].set_xlabel('Time (seconds)', fontsize=11)
    axes[0].set_ylabel('RTT (ms)', fontsize=11)
    axes[0].set_title('RTT Over Time', fontsize=12, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Distribuição de RTT
    all_rtt = []
    labels = []
    
    if data_21:
        rtt_vals_21 = [d.get('rtt', 0) for d in data_21 if d.get('rtt', 0) > 0]
        if rtt_vals_21:
            all_rtt.append(rtt_vals_21)
            labels.append('10.0.0.21')
    
    if data_22:
        rtt_vals_22 = [d.get('rtt', 0) for d in data_22 if d.get('rtt', 0) > 0]
        if rtt_vals_22:
            all_rtt.append(rtt_vals_22)
            labels.append('10.0.0.22')
    
    if all_rtt:
        axes[1].boxplot(all_rtt, labels=labels, patch_artist=True)
        axes[1].set_ylabel('RTT (ms)', fontsize=11)
        axes[1].set_title('RTT Distribution', fontsize=12, fontweight='bold')
        axes[1].grid(True, alpha=0.3, axis='y')
        
        # Adicionar estatísticas
        for i, rtt_vals in enumerate(all_rtt):
            median = np.median(rtt_vals)
            mean = np.mean(rtt_vals)
            axes[1].text(i+1, np.max(rtt_vals) * 0.9, 
                        f'Mean: {mean:.0f}ms\nMedian: {median:.0f}ms',
                        ha='center', fontsize=9,
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated: {output_file}")

def plot_retransmissions(data_21, data_22, output_file):
    """Gráfico de retransmissões TCP"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Retransmissões acumuladas
    if data_21:
        retrans_21 = np.cumsum([d['retransmits'] for d in data_21])
        times_21 = [d['end_time'] for d in data_21]
        ax.plot(times_21, retrans_21, label='10.0.0.21', 
                color='blue', linewidth=2, marker='o', markersize=3)
    
    if data_22:
        retrans_22 = np.cumsum([d['retransmits'] for d in data_22])
        times_22 = [d['end_time'] for d in data_22]
        ax.plot(times_22, retrans_22, label='10.0.0.22', 
                color='red', linewidth=2, marker='s', markersize=3)
    
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('Cumulative TCP Retransmissions', fontsize=12)
    ax.set_title('TCP Retransmissions Over Time', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    # Adicionar totais
    total_text = ""
    if data_21:
        total_21 = sum([d['retransmits'] for d in data_21])
        total_text += f"10.0.0.21: {total_21} retransmissions\n"
    
    if data_22:
        total_22 = sum([d['retransmits'] for d in data_22])
        total_text += f"10.0.0.22: {total_22} retransmissions"
    
    ax.text(0.02, 0.98, total_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated: {output_file}")

def plot_congestion_window(data_21, data_22, output_file):
    """Gráfico da janela de congestionamento TCP"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    if data_21:
        cwnd_21 = [d.get('snd_cwnd', 0) for d in data_21 if d.get('snd_cwnd', 0) > 0]
        times_21 = [d['end_time'] for d in data_21 if d.get('snd_cwnd', 0) > 0]
        if cwnd_21:
            ax.plot(times_21, cwnd_21, label='10.0.0.21', 
                    color='blue', linewidth=1.5, alpha=0.8)
    
    if data_22:
        cwnd_22 = [d.get('snd_cwnd', 0) for d in data_22 if d.get('snd_cwnd', 0) > 0]
        times_22 = [d['end_time'] for d in data_22 if d.get('snd_cwnd', 0) > 0]
        if cwnd_22:
            ax.plot(times_22, cwnd_22, label='10.0.0.22', 
                    color='red', linewidth=1.5, alpha=0.8)
    
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('Congestion Window (bytes)', fontsize=12)
    ax.set_title('TCP Congestion Window Over Time', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated: {output_file}")

def plot_summary_dashboard(data_21, data_22, output_file):
    """Dashboard resumo com múltiplas métricas"""
    fig = plt.figure(figsize=(16, 10))
    
    # 1. Throughput (subplot superior)
    ax1 = plt.subplot(2, 2, 1)
    if data_21:
        times_21 = [d['end_time'] for d in data_21]
        throughput_21 = [d['bits_per_second'] for d in data_21]
        ax1.plot(times_21, throughput_21, label='10.0.0.21', color='blue', linewidth=1.5)
    if data_22:
        times_22 = [d['end_time'] for d in data_22]
        throughput_22 = [d['bits_per_second'] for d in data_22]
        ax1.plot(times_22, throughput_22, label='10.0.0.22', color='red', linewidth=1.5)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Throughput (Gbps)')
    ax1.set_title('Throughput')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. RTT (subplot superior direito)
    ax2 = plt.subplot(2, 2, 2)
    if data_21:
        rtt_21 = [d.get('rtt', 0) for d in data_21 if d.get('rtt', 0) > 0]
        if rtt_21:
            ax2.hist(rtt_21, bins=30, alpha=0.5, label='10.0.0.21', color='blue')
    if data_22:
        rtt_22 = [d.get('rtt', 0) for d in data_22 if d.get('rtt', 0) > 0]
        if rtt_22:
            ax2.hist(rtt_22, bins=30, alpha=0.5, label='10.0.0.22', color='red')
    ax2.set_xlabel('RTT (ms)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('RTT Distribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Retransmissões por segundo (subplot inferior esquerdo)
    ax3 = plt.subplot(2, 2, 3)
    if data_21:
        retrans_per_sec_21 = [d['retransmits'] for d in data_21]
        times_21_retrans = [d['end_time'] for d in data_21]
        ax3.bar(times_21_retrans, retrans_per_sec_21, alpha=0.5, label='10.0.0.21', 
                color='blue', width=0.8)
    if data_22:
        retrans_per_sec_22 = [d['retransmits'] for d in data_22]
        times_22_retrans = [d['end_time'] for d in data_22]
        ax3.bar(times_22_retrans, retrans_per_sec_22, alpha=0.5, label='10.0.0.22', 
                color='red', width=0.8)
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Retransmissions')
    ax3.set_title('TCP Retransmissions per Second')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Estatísticas gerais (subplot inferior direito)
    ax4 = plt.subplot(2, 2, 4)
    ax4.axis('off')
    
    # Coletar estatísticas
    stats_data = []
    
    for ip, data in [('10.0.0.21', data_21), ('10.0.0.22', data_22)]:
        if data:
            throughputs = [d['bits_per_second'] for d in data]
            rtts = [d.get('rtt', 0) for d in data if d.get('rtt', 0) > 0]
            retrans_total = sum([d['retransmits'] for d in data])
            
            stats_data.append({
                'IP': ip,
                'Avg Throughput (Gbps)': f"{np.mean(throughputs):.2f}",
                'Max Throughput (Gbps)': f"{max(throughputs):.2f}",
                'Min Throughput (Gbps)': f"{min(throughputs):.2f}",
                'Avg RTT (ms)': f"{np.mean(rtts):.0f}" if rtts else "N/A",
                'Total Retransmissions': f"{retrans_total}"
            })
    
    if stats_data:
        df_stats = pd.DataFrame(stats_data)
        table = ax4.table(cellText=df_stats.values, colLabels=df_stats.columns,
                         cellLoc='center', loc='center',
                         colWidths=[0.15, 0.2, 0.2, 0.2, 0.15, 0.2])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        
        # Colorir cabeçalho
        for (i, j), cell in table.get_celld().items():
            if i == 0:
                cell.set_facecolor('#40466e')
                cell.set_text_props(weight='bold', color='white')
    
    ax4.set_title('Summary Statistics', fontsize=12, fontweight='bold', pad=20)
    
    plt.suptitle('iPerf3 Network Performance Dashboard', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated: {output_file}")

def print_summary_statistics(data, target_ip):
    """Imprime estatísticas resumidas no console"""
    if not data:
        print(f"No data available for {target_ip}")
        return
    
    throughputs = [d['bits_per_second'] for d in data]
    rtts = [d.get('rtt', 0) for d in data if d.get('rtt', 0) > 0]
    retrans_total = sum([d['retransmits'] for d in data])
    
    print(f"\n{'='*50}")
    print(f"iPerf3 Statistics - Target: {target_ip}")
    print(f"{'='*50}")
    print(f"Throughput:")
    print(f"  - Average: {np.mean(throughputs):.2f} Gbps")
    print(f"  - Maximum: {max(throughputs):.2f} Gbps")
    print(f"  - Minimum: {min(throughputs):.2f} Gbps")
    print(f"  - Std Dev: {np.std(throughputs):.2f} Gbps")
    
    if rtts:
        print(f"\nRTT (Round Trip Time):")
        print(f"  - Average: {np.mean(rtts):.0f} ms")
        print(f"  - Maximum: {max(rtts):.0f} ms")
        print(f"  - Minimum: {min(rtts):.0f} ms")
        print(f"  - Median: {np.median(rtts):.0f} ms")
    
    print(f"\nTCP Retransmissions:")
    print(f"  - Total: {retrans_total}")
    print(f"  - Average per second: {retrans_total / len(data):.2f}")

def main():
    parser = argparse.ArgumentParser(
        description='Generate graphs from iPerf3 JSON output files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Using specific files
  python script.py --json-21 iperf_10.0.0.21.json --json-22 iperf_10.0.0.22.json
  
  # Using patterns (glob)
  python script.py --json-21 "iperf_10.0.0.21*.json" --json-22 "iperf_10.0.0.22*.json"
  
  # Using /tmp directory
  python script.py --json-21 /tmp/iperf_10.0.0.21*.json --json-22 /tmp/iperf_10.0.0.22*.json
  
  # Using only one file
  python script.py --json-21 iperf_10.0.0.21.json
        '''
    )
    
    parser.add_argument('--json-21', type=str, required=True, 
                       help='iPerf3 JSON file for target 10.0.0.21')
    parser.add_argument('--json-22', type=str, 
                       help='iPerf3 JSON file for target 10.0.0.22 (optional)')
    parser.add_argument('--output-dir', type=str, default='.', 
                       help='Output directory for graphs (default: current directory)')
    
    args = parser.parse_args()
    
    # Criar diretório de saída se não existir
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=" * 60)
    print("📊 iPerf3 Metrics Visualization Tool")
    print("=" * 60)
    
    # Carregar arquivos JSON
    print("\n📂 Loading iPerf3 JSON files...")
    
    # Processar arquivo para 10.0.0.21
    json_21_files = glob.glob(args.json_21) if '*' in args.json_21 else [args.json_21]
    data_21_raw = None
    if json_21_files:
        data_21_raw = load_iperf_json(json_21_files[0])
    else:
        print(f"⚠️  No files found for pattern: {args.json_21}")
    
    # Processar arquivo para 10.0.0.22 (opcional)
    data_22_raw = None
    if args.json_22:
        json_22_files = glob.glob(args.json_22) if '*' in args.json_22 else [args.json_22]
        if json_22_files:
            data_22_raw = load_iperf_json(json_22_files[0])
        else:
            print(f"⚠️  No files found for pattern: {args.json_22}")
    
    if not data_21_raw and not data_22_raw:
        print("\n❌ No iPerf3 JSON files could be loaded!")
        sys.exit(1)
    
    # Extrair dados dos intervalos
    print("\n📊 Extracting interval data...")
    interval_data = {}
    
    if data_21_raw:
        interval_data['10.0.0.21'] = extract_interval_data(data_21_raw, '10.0.0.21')
        print(f"  - 10.0.0.21: {len(interval_data['10.0.0.21'])} intervals extracted")
    
    if data_22_raw:
        interval_data['10.0.0.22'] = extract_interval_data(data_22_raw, '10.0.0.22')
        print(f"  - 10.0.0.22: {len(interval_data['10.0.0.22'])} intervals extracted")
    
    # Imprimir estatísticas
    for ip, data in interval_data.items():
        print_summary_statistics(data, ip)
    
    # Gerar gráficos
    print("\n🎨 Generating graphs...")
    print("-" * 40)
    
    data_21 = interval_data.get('10.0.0.21')
    data_22 = interval_data.get('10.0.0.22')
    
    # Gráfico 1: Throughput Comparison
    if data_21 and data_22:
        output_file = os.path.join(args.output_dir, 'iperf3_throughput_comparison.png')
        plot_throughput_comparison(data_21, data_22, output_file)
    elif data_21:
        output_file = os.path.join(args.output_dir, 'iperf3_throughput_10.0.0.21.png')
        plot_throughput_comparison(data_21, None, output_file)
    elif data_22:
        output_file = os.path.join(args.output_dir, 'iperf3_throughput_10.0.0.22.png')
        plot_throughput_comparison(None, data_22, output_file)
    
    # Gráfico 2: RTT Analysis
    if data_21 or data_22:
        output_file = os.path.join(args.output_dir, 'iperf3_rtt_analysis.png')
        plot_rtt_analysis(data_21, data_22, output_file)
    
    # Gráfico 3: Retransmissions
    if data_21 or data_22:
        output_file = os.path.join(args.output_dir, 'iperf3_retransmissions.png')
        plot_retransmissions(data_21, data_22, output_file)
    
    # Gráfico 4: Congestion Window
    if data_21 or data_22:
        output_file = os.path.join(args.output_dir, 'iperf3_congestion_window.png')
        plot_congestion_window(data_21, data_22, output_file)
    
    # Gráfico 5: Summary Dashboard
    if data_21 or data_22:
        output_file = os.path.join(args.output_dir, 'iperf3_summary_dashboard.png')
        plot_summary_dashboard(data_21, data_22, output_file)
    
    print("\n" + "=" * 60)
    print("✅ All iPerf3 graphs generated successfully!")
    print(f"📁 Output directory: {args.output_dir}")
    print("=" * 60)
    print("\n📁 Generated files:")
    if os.path.exists(os.path.join(args.output_dir, 'iperf3_throughput_comparison.png')):
        print("  - iperf3_throughput_comparison.png")
    if os.path.exists(os.path.join(args.output_dir, 'iperf3_rtt_analysis.png')):
        print("  - iperf3_rtt_analysis.png")
    if os.path.exists(os.path.join(args.output_dir, 'iperf3_retransmissions.png')):
        print("  - iperf3_retransmissions.png")
    if os.path.exists(os.path.join(args.output_dir, 'iperf3_congestion_window.png')):
        print("  - iperf3_congestion_window.png")
    if os.path.exists(os.path.join(args.output_dir, 'iperf3_summary_dashboard.png')):
        print("  - iperf3_summary_dashboard.png")
    print("\n💡 Key Metrics Analyzed:")
    print("  • Throughput (bandwidth in Gbps)")
    print("  • RTT (Round Trip Time in ms)")
    print("  • TCP Retransmissions")
    print("  • Congestion Window size")
    print("=" * 60)

if __name__ == "__main__":
    import sys
    main()
