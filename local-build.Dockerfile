# https://quay.io/repository/fedora/nodejs-20?tab=tags
FROM quay.io/fedora/nodejs-20@sha256:b19625cb64a1c778f23d4123e637764212712db0630730935fa0aac785476661 AS base

USER 0

RUN dnf install -y \
    make-4.4.1 \
    python3-3.11.7 \
    python3-pip-22.3.1 \
    -- &&\
    dnf clean all &&\
    npm install -g aws-cdk@2.1007.0

COPY Makefile /tmp/Makefile
COPY portal-cdk /tmp/portal-cdk

WORKDIR /tmp/portal-cdk
RUN python3 -m pip install --no-cache-dir -r requirements.txt &&\
    cdk synth

USER 1001
