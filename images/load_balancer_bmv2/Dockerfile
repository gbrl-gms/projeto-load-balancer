FROM p4lang/behavioral-model:latest

RUN apt-get update && apt-get install -y --no-install-recommends \
	bash \
	iproute2 \
	iputils-ping \
	&& rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash"]
