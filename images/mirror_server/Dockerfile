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
    wget \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY nginx.conf /etc/nginx/nginx.conf
RUN mkdir -p /usr/share/nginx/html/videos
WORKDIR /usr/share/nginx/html/videos

RUN curl -o BigBuckBunny.mp4 https://download.blender.org/peach/bigbuckbunny_movies/BigBuckBunny_320x180.mp4 

RUN ffmpeg -i BigBuckBunny.mp4 -map 0 -map 0 -c:a aac -c:v libx264 -b:v:0 800k -s:v:0 640x360 -adaptation_sets "id=0,streams=v id=1,streams=a" -preset veryfast -f dash video.mpd
EXPOSE 80 5000

CMD nginx -g 'daemon off;'
