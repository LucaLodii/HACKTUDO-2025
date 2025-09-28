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
COPY <<EOF /app/start.sh
#!/bin/sh
# Start virtual display for headless Chrome
Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset > /dev/null 2>&1 &
export DISPLAY=:99

# Wait for Xvfb to start
sleep 2

# Start the application
exec node server.js
EOF

RUN chmod +x /app/start.sh

EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

CMD ["/app/start.sh"]