FROM ubuntu:18.04
LABEL Description="Ubuntu 18.04 FreePN" Version="1.0"
RUN apt-get update && apt-get install -y \
  software-properties-common 
RUN add-apt-repository -y -s ppa:nerdboy/embedded
RUN apt-get install -y python3-fpnd
