FROM nginx:latest

RUN apt-get update && apt-get install -y \
    net-tools \
    iputils-ping \
    iproute2 \
    bash \
    && rm -rf /var/lib/apt/lists/*

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80 5000

CMD nginx -g 'daemon off;'
