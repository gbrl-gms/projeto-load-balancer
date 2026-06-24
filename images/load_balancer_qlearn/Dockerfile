FROM nginx:latest

RUN apt-get update && apt-get install -y \
    net-tools \
    iputils-ping \
    iproute2 \
    bash \
    git \
    python3 \
    python3-numpy \
    vlc \
    && rm -rf /var/lib/apt/lists/*

COPY nginx.conf /etc/nginx/nginx.conf
RUN sed -i 's/geteuid/getppid/' /usr/bin/vlc

RUN mkdir -p /vagrant/logs
WORKDIR /app
RUN git clone https://github.com/leandrocalmeida/wave
COPY wave_config wave/run_wave.sh

COPY upstream-latency.sh /upstream-latency.sh 
COPY qlearn.py /qlearn.py

EXPOSE 80 5000

CMD nginx -g 'daemon off;'
