FROM python:3

RUN pip install --no-cache-dir cryptography==2.4.2 click fabric

WORKDIR /sinzlab_tools

COPY . .

RUN python setup.py install