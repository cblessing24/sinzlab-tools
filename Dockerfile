FROM python:3

RUN pip install --no-cache-dir cryptography==2.4.2 click fabric

RUN mkdir -p -m 0600 ~/.ssh
COPY config /root/.ssh/

WORKDIR /sinzlab-tools

COPY . .

RUN python setup.py install