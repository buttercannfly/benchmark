# default base image: xzhao9/gcp-a100-runner-dind:latest
ARG BASE_IMAGE=docker.io/xzhao9/gcp-a100-runner-dind@sha256:dad740f8bab2b79520b78bac9a32d6ae7aea51d2f1519366f510a6f938f7b575
FROM ${BASE_IMAGE}

ENV CONDA_ENV=torchbench
ENV SETUP_SCRIPT=/workspace/setup_instance.sh
ARG TORCHBENCH_BRANCH=${TORCHBENCH_BRANCH:-main}
ARG FORCE_DATE=${FORCE_DATE}


# Checkout Torchbench and submodules
RUN git clone --recurse-submodules -b "${TORCHBENCH_BRANCH}" --single-branch \
    https://github.com/buttercannfly/benchmark /workspace/benchmark

# Setup conda env and CUDA
RUN cd /workspace/benchmark && \
    . ${SETUP_SCRIPT} && \
    python ./utils/python_utils.py --create-conda-env ${CONDA_ENV} && \
    echo "if [ -z \${CONDA_ENV} ]; then export CONDA_ENV=${CONDA_ENV}; fi" >> /workspace/setup_instance.sh && \
    echo "conda activate \${CONDA_ENV}" >> /workspace/setup_instance.sh

RUN cd /workspace/benchmark && \
    . ${SETUP_SCRIPT} && \
    sudo python ./utils/cuda_utils.py --setup-cuda-softlink

RUN cd /workspace/benchmark && \
    . ${SETUP_SCRIPT} && \
    python utils/cuda_utils.py --install-torch-deps && \ 
    python utils/cuda_utils.py --install-torch-nightly

# Check the installed version of nightly if needed

# Install TorchBench conda and python dependencies
RUN cd /workspace/benchmark && \
    . ${SETUP_SCRIPT} && \
    python utils/cuda_utils.py --install-torchbench-deps

# Install TorchAO benchmark
# RUN cd /workspace/benchmark && \
#     . ${SETUP_SCRIPT} && \
#     python install.py --userbenchmark torchao

# Install Torchbench models
RUN cd /workspace/benchmark && \
    . ${SETUP_SCRIPT} && \
    python install.py
