#!/bin/bash

docker run --name containernet -it --privileged \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v $(pwd):/home/projeto-load-balancer \
    containernet/containernet:latest /bin/bash
