FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# hadolint ignore=DL3033,SC1035

RUN mkdir /cdk && mkdir /build
WORKDIR /cdk

### Basic system setup
# nodejs: For installing AWS CDK
# unzip vim tar gzip git make jq python3-pip findutils: Basic Packages
# python3-setuptools: Required for both `dnf-plugins-core`, AND installing python packages later
# dnf-plugins-core: Required for `yum config-manager --add-repo`
# hadolint ignore=DL3033
RUN yum upgrade -y && \
    yum install -y \
        nodejs \
        unzip \
        vim \
        tar \
        gzip \
        git \
        make \
        jq \
        python3-pip \
        findutils \
        python3-setuptools \
        dnf-plugins-core && \
    yum clean all &&  \
    rm -rf /var/cache/yum

# Install node/aws-cdk
# hadolint ignore=DL3016
RUN npm install -g npm && \
    npm install -g aws-cdk

# Create/setup .bashrc for root
# hadolint ignore=SC2028
RUN cp /etc/bashrc ~/.bashrc && \
    echo 'export PS1="\[\e[m\]\[\e[35m\][ \[\e[31m\]\u\[\e[35m\]@\[\e[32m\]\h\[\e[35m\]:\[\e[36m\]\w\[\e[35m\] ]\\$\[\e[m\] "' >> ~/.bashrc

# Install cdk client software
COPY ./build/cdk.requirements.txt /build/requirements.txt

# hadolint ignore=DL3013
RUN python3 -m pip install --no-cache-dir --upgrade wheel && \
    python3 -m pip install --no-cache-dir -r /build/requirements.txt
ENV PYTHONPATH="/cdk_utils:"

# Cleanup:
RUN yum clean all && rm -rf /var/cache/yum

COPY ./build /build
ENTRYPOINT ["/bin/bash"]