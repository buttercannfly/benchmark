FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/conda/bin:${PATH}"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    ca-certificates \
    build-essential \
    libjpeg-dev \ 
    libpng-dev \
    cmake \
    iproute2 \
    
    && rm -rf /var/lib/apt/lists/*

# Install Miniconda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    /bin/bash /tmp/miniconda.sh -b -p /opt/conda && \
    rm /tmp/miniconda.sh && \
    /opt/conda/bin/conda clean -ya

# Create conda environment with Python 3.11
RUN conda install -y python=3.11 && \
    conda clean -ya

# Install NVIDIA libraries
RUN conda install -y -c pytorch magma-cuda121 && \
    conda clean -ya

# Install PyTorch, torchvision, and torchaudio
RUN conda install -y pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch-nightly -c nvidia && \
    conda clean -ya

# Clone and install the benchmark suite
WORKDIR /app
RUN git clone https://github.com/buttercannfly/benchmark && \
    cd benchmark && \
    python install.py

# Set the working directory
WORKDIR /app/benchmark

# Set default command to activate the environment and provide a shell
CMD ["python", "-m", "http.server"]

# Optional: Add an entrypoint script for running specific benchmarks
# COPY entrypoint.sh /entrypoint.sh
# RUN chmod +x /entrypoint.sh
# ENTRYPOINT ["/entrypoint.sh"]