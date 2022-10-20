FROM ubuntu:22.04

ARG INSTALL_PATH="/opt/tn4-player"
ENV PATH="/opt/tn4-player/bin:$HOME/.local/bin:$PATH"

RUN apt-get update \
 && apt-get upgrade -y \
 && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
      git \
      python3 \
      python3-pip \
 && apt-get clean \
 && rm -rf /var/lib/apt/*

COPY . ${INSTALL_PATH}
WORKDIR ${INSTALL_PATH}

RUN python3 -m pip install --upgrade pipenv \
 && pipenv requirements > requirements.txt \
 && python3 -m pip install -r requirements.txt

RUN pip install \
      --extra-index-url=https://ansible.github.io/pylibssh/simple/ \
      --pre \
      ansible-pylibssh
