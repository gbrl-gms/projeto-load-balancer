FROM nginx:latest

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    procps \
    && rm -rf /var/lib/apt/lists/*

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80 5000

CMD nginx -g 'daemon off;'
