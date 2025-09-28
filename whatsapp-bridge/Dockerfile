FROM node:18-alpine

# Install Chrome and dependencies for Render.com
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
    udev \
    ttf-opensans \
    && rm -rf /var/cache/apk/*

# Set environment variables for Puppeteer
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser \
    NODE_OPTIONS="--max-old-space-size=1024" \
    DISPLAY=:99

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with optimizations for Render
RUN npm install --only=production --silent && \
    npm cache clean --force && \
    rm -rf /tmp/*

# Copy source code
COPY . .

# Create auth directory
RUN mkdir -p /app/.wwebjs_auth

# Create startup script for Render
RUN echo '#!/bin/sh\n\
# Start virtual display for headless Chrome\n\
Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset > /dev/null 2>&1 &\n\
export DISPLAY=:99\n\
\n\
# Wait for Xvfb to start\n\
sleep 2\n\
\n\
# Start the application\n\
exec node server.js' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

CMD ["/app/start.sh"]