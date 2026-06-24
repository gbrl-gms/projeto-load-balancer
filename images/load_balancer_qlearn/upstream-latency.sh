#!/bin/bash

# Roda em um loop infinito
while true; do
    # Executa o ping e extrai o valor 'avg' (segundo valor após o igual)
    ping_21=$(ping -c 1 10.0.0.21 | grep 'rtt min/avg/max/mdev' | awk -F'[/ ]' '{print $8}')
    ping_22=$(ping -c 1 10.0.0.22 | grep 'rtt min/avg/max/mdev' | awk -F'[/ ]' '{print $8}')

    # Define TIMEOUT caso o host esteja inacessível
    ping_21=${ping_21:-"TIMEOUT"}
    ping_22=${ping_22:-"TIMEOUT"}

    # Sobrescreve o arquivo com os dados em tempo real
    cat << EOF > /tmp/upstream_latency
${ping_21}
${ping_22}
EOF

    # Aguarda 1 segundo antes da próxima verificação (ajuste se precisar de mais tempo)
    sleep 1
done
