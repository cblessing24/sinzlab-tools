FROM python:3

RUN pip install --no-cache-dir cryptography==2.4.2 click fabric

WORKDIR /root/sinzlab-tools

COPY . .

RUN python setup.py install