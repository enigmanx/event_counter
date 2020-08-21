FROM ubuntu:18.04

RUN apt update -y
RUN apt install python3-pip -y
RUN apt install curl -y

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 5000