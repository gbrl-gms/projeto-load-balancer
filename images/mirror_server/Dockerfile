FROM nginx:latest

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    procps \
    net-tools \
    iputils-ping \
    iproute2 \
    bash \
    iperf3 \
    xmlstarlet \
    && rm -rf /var/lib/apt/lists/*

COPY nginx.conf /etc/nginx/nginx.conf
RUN mkdir /var/www/html/videos

COPY download /app/download
RUN chmod +x /app/download
RUN /app/download

EXPOSE 80 5000

CMD nginx -g 'daemon off;'
