FROM alpine/curl:latest

RUN apk add --no-cache \
    net-tools \
    iputils \
    iproute2 \
    bash \
    git \
    python3 \
    vlc \
    xvfb \
    iperf3

RUN sed -i 's/geteuid/getppid/' /usr/bin/vlc
RUN mkdir -p /scripts
RUN mkdir -p /tmp/.X11-unix 
RUN chmod 1777 /tmp/.X11-unix

WORKDIR /scripts

RUN git clone https://github.com/leandrocalmeida/wave

COPY wave_config wave/run_wave.sh

CMD /bin/bash
