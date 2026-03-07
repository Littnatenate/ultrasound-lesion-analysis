# Use Python 3.10 slim as the base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for OpenCV, PyTorch, and compiling Detectron2
RUN apt-get update && apt-get install -y \
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

# Install dependencies using uv. We force the CPU version of PyTorch for standard web hosting.
RUN uv pip install --system --no-cache -r requirements_docker.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Install Detectron2 (Linux wheel build compatible with PyTorch 2.3 CPU)
RUN uv pip install --system --no-cache 'git+https://github.com/facebookresearch/detectron2.git'

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
