FROM alpine/curl:latest

RUN apk add --no-cache \
    net-tools \
    iputils \
    iproute2 \
    bash \
    git \
    python3 \
    vlc \
    iperf3

RUN sed -i 's/geteuid/getppid/' /usr/bin/vlc

WORKDIR /app

RUN git clone https://github.com/leandrocalmeida/wave

COPY wave_config wave/run_wave.sh

CMD /bin/bash
