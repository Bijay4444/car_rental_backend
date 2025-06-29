# Stage 1: Builder stage for dependencies and compilation
FROM python:3.10.14-slim-bookworm AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies with security updates
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    gcc \
    libc6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Upgrade pip to latest secure version
RUN pip install --upgrade pip

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production stage (much smaller)
FROM python:3.10.14-slim-bookworm AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=car_management_system.settings

# Install security updates and only runtime dependencies
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    ca-certificates \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/* \
    && rm -rf /var/cache/apt/*

# Create non-root user for security
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /bin/bash appuser && \
    mkdir -p /app/media /app/staticfiles && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/staticfiles

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=appuser:appuser . /app/

# Switch to non-root user
USER appuser

# NOTE: We'll collect static files at runtime, not build time
# This avoids environment variable issues during build

# Expose the application port
EXPOSE 8080

# Health check for container monitoring
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/admin/ || exit 1

# Create startup script that collects static files and starts gunicorn
RUN echo '#!/bin/bash\n\
    echo "🚀 Starting Car Rental API..."\n\
    echo "📁 Collecting static files..."\n\
    python manage.py collectstatic --noinput --clear\n\
    echo "🔄 Running migrations..."\n\
    python manage.py migrate --noinput\n\
    echo "🎯 Starting Gunicorn server..."\n\
    exec gunicorn --bind 0.0.0.0:8080 --workers 3 --timeout 120 car_management_system.wsgi:application' > /app/start.sh \
    && chmod +x /app/start.sh

# Start the application using our startup script
CMD ["/app/start.sh"]