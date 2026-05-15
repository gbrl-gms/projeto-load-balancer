import psutil
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/metrics')
def get_metrics():
    # coleta direitinho o uso de cpu e memoria que vai alimentar a tabela Q
    return jsonify({
        'cpu': psutil.cpu_percent(interval=1),
        'memory': psutil.virtual_memory().percent
    })

if __name__ == '__main__':
    # roda numa porta diferente pra nao ter risco de conflitar com o serviço principal
    app.run(host='0.0.0.0', port=81)