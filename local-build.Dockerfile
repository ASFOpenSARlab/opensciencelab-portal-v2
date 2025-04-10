FROM quay.io/fedora/nodejs-20 AS base

USER root
WORKDIR /tmp

RUN yum install -y make python python-pip &&\
    npm install -g aws-cdk

COPY Makefile Makefile
COPY portal-cdk portal-cdk

RUN cd portal-cdk &&\
    python -m pip install -r requirements.txt &&\
    cdk synth
