FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install system dependencies for WhatsApp Web.js + Render.com compatibility
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    dbus \
    xvfb \
    curl \
    && rm -rf /var/cache/apk/*

# Tell Puppeteer to skip installing Chromium. We'll be using the installed package.
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser \
    NODE_OPTIONS="--max-old-space-size=1024" \
    DISPLAY=:99

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Create directory for WhatsApp session data
RUN mkdir -p /app/.wwebjs_auth

# Expose port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

# Create startup script for Render.com
RUN echo '#!/bin/sh\n\
# Start virtual display for headless Chrome on Render\n\
if [ "$RENDER" = "true" ]; then\n\
    echo "🌐 Starting Xvfb for Render.com..."\n\
    Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset &\n\
    export DISPLAY=:99\n\
    sleep 2\n\
fi\n\
\n\
# Start the application\n\
exec node server.js' > /app/start.sh && chmod +x /app/start.sh

# Start the application
CMD ["/app/start.sh"]

