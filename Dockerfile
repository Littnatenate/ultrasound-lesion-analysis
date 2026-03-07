# Use Python 3.10 bullseye as the base image (more stable apt repositories)
FROM python:3.10-bullseye

# Set working directory
WORKDIR /app

# Install system dependencies required for OpenCV, PyTorch, and compiling Detectron2
RUN apt-get clean && apt-get update --fix-missing && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install uv (astral-sh/uv) to massively speed up pip installs
RUN pip install --no-cache-dir uv

# Copy the requirements file first to cache the dependency installation layer
COPY requirements_docker.txt .

# Upgrade pip to properly handle modern dependency resolution
RUN pip install --no-cache-dir --upgrade pip

# 1. Install PyTorch CPU FIRST and completely separately to avoid crashing Render's 512MB RAM limit!
RUN pip install --no-cache-dir torch==2.3.1+cpu torchvision==0.18.1+cpu --extra-index-url https://download.pytorch.org/whl/cpu

# 2. Install the rest of the standard dependencies
RUN pip install --no-cache-dir -r requirements_docker.txt

# Install Detectron2 (Requires --no-build-isolation so it can see the torch we just installed)
RUN pip install --no-cache-dir --no-build-isolation 'git+https://github.com/facebookresearch/detectron2.git'

# Copy the entire project into the container
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose the port
EXPOSE 8000

# The launcher script handles the startup. For Docker, we just run uvicorn directly
# Note: We run the API from the web/backend directory
CMD ["uvicorn", "web.backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
