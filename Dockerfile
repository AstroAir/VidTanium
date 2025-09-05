# Multi-stage Dockerfile for VidTanium
# Supports both GUI and headless modes

# Build stage
FROM python:3.11-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY . .

# Build the application
RUN uv run python -m build

# Production stage - GUI version
FROM python:3.11-slim as production-gui

# Install system dependencies for GUI applications
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxrender1 \
    libxrandr2 \
    libxss1 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libxi6 \
    libxtst6 \
    libqt6core6 \
    libqt6gui6 \
    libqt6widgets6 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 vidtanium

# Set working directory
WORKDIR /app

# Copy built application from builder stage
COPY --from=builder /app/dist/*.whl /tmp/
COPY --from=builder /app/src ./src
COPY --from=builder /app/config ./config
COPY --from=builder /app/main.py ./

# Install the application
RUN pip install /tmp/*.whl && rm /tmp/*.whl

# Create directories for user data
RUN mkdir -p /app/downloads /app/config /app/logs && \
    chown -R vidtanium:vidtanium /app

# Switch to non-root user
USER vidtanium

# Set environment variables
ENV PYTHONPATH=/app
ENV VIDTANIUM_OUTPUT_DIR=/app/downloads
ENV VIDTANIUM_CONFIG_DIR=/app/config
ENV VIDTANIUM_LOG_LEVEL=INFO
ENV QT_QPA_PLATFORM=xcb
ENV DISPLAY=:99

# Expose volume for downloads
VOLUME ["/app/downloads", "/app/config"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "main.py", "--no-gui"]

# Production stage - Headless version
FROM python:3.11-slim as production-headless

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 vidtanium

# Set working directory
WORKDIR /app

# Copy built application from builder stage
COPY --from=builder /app/dist/*.whl /tmp/
COPY --from=builder /app/src ./src
COPY --from=builder /app/config ./config
COPY --from=builder /app/main.py ./

# Install the application (minimal dependencies for headless)
RUN pip install /tmp/*.whl && rm /tmp/*.whl

# Create directories for user data
RUN mkdir -p /app/downloads /app/config /app/logs && \
    chown -R vidtanium:vidtanium /app

# Switch to non-root user
USER vidtanium

# Set environment variables
ENV PYTHONPATH=/app
ENV VIDTANIUM_OUTPUT_DIR=/app/downloads
ENV VIDTANIUM_CONFIG_DIR=/app/config
ENV VIDTANIUM_LOG_LEVEL=INFO
ENV VIDTANIUM_NO_GUI=true

# Expose volume for downloads
VOLUME ["/app/downloads", "/app/config"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "main.py", "--no-gui"]

# Development stage
FROM python:3.11-slim as development

# Install development dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxrender1 \
    libxrandr2 \
    libxss1 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libxi6 \
    libxtst6 \
    libqt6core6 \
    libqt6gui6 \
    libqt6widgets6 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Create non-root user
RUN useradd -m -u 1000 vidtanium

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install all dependencies including dev
RUN uv sync --dev

# Create directories
RUN mkdir -p /app/downloads /app/config /app/logs && \
    chown -R vidtanium:vidtanium /app

# Switch to non-root user
USER vidtanium

# Set environment variables
ENV PYTHONPATH=/app
ENV VIDTANIUM_OUTPUT_DIR=/app/downloads
ENV VIDTANIUM_CONFIG_DIR=/app/config
ENV VIDTANIUM_LOG_LEVEL=DEBUG
ENV QT_QPA_PLATFORM=xcb
ENV DISPLAY=:99

# Expose volume for development
VOLUME ["/app", "/app/downloads", "/app/config"]

# Default command for development
CMD ["bash"]
