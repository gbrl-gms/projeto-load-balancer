import psutil
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/metrics')
def metrics():
    # Coleta os dados de uso de CPU e memória que servirão de entrada para o estado da IA
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent

    return jsonify({
        'cpu': cpu_usage,
        'memory': memory_usage
    })

if __name__ == '__main__':
    # Roda em uma porta dedicada (81) para não conflitar com o tráfego do serviço principal (80)
    app.run(host='0.0.0.0', port=81)
