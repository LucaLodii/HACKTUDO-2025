/**
 * WhatsApp Web.js Bridge for sofIA Payment Agent
 *
 * This Node.js server bridges WhatsApp Web.js with the Python sofIA agent,
 * enabling real-time WhatsApp messaging for payment processing.
 */

const { Client, LocalAuth, MessageTypes } = require('whatsapp-web.js');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const qrcode = require('qrcode-terminal');
const { Server } = require('socket.io');
const http = require('http');

class SofiaWhatsAppBridge {
    constructor() {
        this.app = express();
        this.server = http.createServer(this.app);
        this.io = new Server(this.server, {
            cors: {
                origin: "*",
                methods: ["GET", "POST"]
            }
        });

        this.whatsappClient = null;
        this.isClientReady = false;
        this.currentQRCode = null;
        this.currentQRCodeImage = null;
        this.sofiaApiUrl = process.env.SOFIA_API_URL || 'http://localhost:8000';

        this.setupExpress();
        this.setupWhatsApp();
        this.setupSocketIO();
    }

    setupExpress() {
        this.app.use(cors());
        this.app.use(express.json());

        // Health check
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                whatsapp_ready: this.isClientReady,
                has_qr_code: !!this.currentQRCode,
                has_qr_image: !!this.currentQRCodeImage,
                service: 'sofIA WhatsApp Bridge'
            });
        });

        // Debug endpoint
        this.app.get('/debug', (req, res) => {
            res.json({
                whatsapp_ready: this.isClientReady,
                has_qr_code: !!this.currentQRCode,
                has_qr_image: !!this.currentQRCodeImage,
                qr_code_length: this.currentQRCode ? this.currentQRCode.length : 0,
                qr_image_length: this.currentQRCodeImage ? this.currentQRCodeImage.length : 0,
                client_exists: !!this.whatsappClient,
                timestamp: new Date().toISOString()
            });
        });

        // Send message endpoint
        this.app.post('/send-message', async (req, res) => {
            try {
                const { to, message } = req.body;

                if (!this.isClientReady) {
                    return res.status(503).json({
                        error: 'WhatsApp client not ready'
                    });
                }

                // Format phone number for WhatsApp (add @c.us suffix)
                const chatId = to.includes('@') ? to : `${to}@c.us`;

                await this.whatsappClient.sendMessage(chatId, message);

                res.json({
                    success: true,
                    message: 'Message sent successfully',
                    to: chatId,
                    text: message
                });

            } catch (error) {
                console.error('Error sending message:', error);
                res.status(500).json({
                    error: 'Failed to send message',
                    details: error.message
                });
            }
        });

        // Get client info
        this.app.get('/client-info', async (req, res) => {
            try {
                if (!this.isClientReady) {
                    return res.status(503).json({
                        error: 'WhatsApp client not ready'
                    });
                }

                const info = this.whatsappClient.info;
                res.json({
                    success: true,
                    client_info: {
                        phone_number: info.wid.user,
                        name: info.pushname,
                        platform: info.platform
                    }
                });

            } catch (error) {
                res.status(500).json({
                    error: 'Failed to get client info',
                    details: error.message
                });
            }
        });

        // QR Code web interface - SIMPLIFIED VERSION
        this.app.get('/qr', (req, res) => {
            const qrImageUrl = this.currentQRCodeImage || '/qr-image';
            const status = this.isClientReady ? '✅ WhatsApp Connected' : '⏳ Waiting for QR Code...';
            const statusClass = this.isClientReady ? 'ready' : 'waiting';
            
            res.send(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>sofIA WhatsApp Bridge</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 20px; background: #f5f5f5; }
                        .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        .logo { font-size: 2em; color: #667eea; margin-bottom: 20px; }
                        .status { padding: 15px; margin: 20px 0; border-radius: 5px; }
                        .waiting { background: #fff3cd; color: #856404; }
                        .ready { background: #d4edda; color: #155724; }
                        .qr-code { margin: 20px 0; }
                        .qr-code img { max-width: 300px; border: 1px solid #ddd; }
                        .instructions { background: #e3f2fd; padding: 20px; border-radius: 5px; text-align: left; margin: 20px 0; }
                        .refresh-btn { background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 10px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="logo">sofIA WhatsApp Bridge</div>
                        <div class="status ${statusClass}">${status}</div>
                        
                        <div class="qr-code">
                            ${this.currentQRCodeImage ? 
                                `<img src="${this.currentQRCodeImage}" alt="QR Code">` :
                                '<p>Generating QR Code...</p>'
                            }
                        </div>
                        
                        <div class="instructions">
                            <h3>📱 How to Connect:</h3>
                            <ol>
                                <li>Open WhatsApp on your phone</li>
                                <li>Tap ⋮ → Linked Devices → Link a Device</li>
                                <li>Scan the QR code above</li>
                            </ol>
                        </div>
                        
                        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
                        <p><small>Page refreshes every 10 seconds</small></p>
                    </div>
                    
                    <script>
                        // Simple auto-refresh
                        setTimeout(() => location.reload(), 10000);
                    </script>
                </body>
                </html>
            `);
        });

        // QR Code as image endpoint
        this.app.get('/qr-image', (req, res) => {
            if (!this.currentQRCode) {
                return res.status(404).json({ error: 'No QR code available' });
            }
            
            // Generate QR code as PNG
            qrcode.toBuffer(this.currentQRCode, { type: 'png' }, (err, buffer) => {
                if (err) {
                    return res.status(500).json({ error: 'Failed to generate QR code image' });
                }
                
                res.set('Content-Type', 'image/png');
                res.send(buffer);
            });
        });
    }

    setupWhatsApp() {
        console.log('🔧 Initializing WhatsApp client...');
        
        // Detect environment and configure Puppeteer accordingly
        const isRender = process.env.RENDER === 'true' || process.env.RENDER_EXTERNAL_URL;
        const executablePath = process.env.PUPPETEER_EXECUTABLE_PATH ||
                              (isRender ? '/usr/bin/chromium-browser' : null);

        console.log(`🌐 Environment: ${isRender ? 'Render.com' : 'Local'}`);
        if (executablePath) console.log(`🔧 Chrome executable: ${executablePath}`);

        // Initialize WhatsApp client with environment-specific settings
        this.whatsappClient = new Client({
            authStrategy: new LocalAuth({
                clientId: "sofia-payment-agent"
            }),
            puppeteer: {
                headless: true,
                executablePath: executablePath,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor,AudioServiceOutOfProcess',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-default-apps',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--memory-pressure-off',
                    '--max_old_space_size=1024',
                    '--disable-background-networking',
                    '--disable-background-sync',
                    '--disable-client-side-phishing-detection',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-hang-monitor',
                    '--disable-prompt-on-repost',
                    '--disable-sync',
                    '--disable-translate',
                    '--metrics-recording-only',
                    '--no-default-browser-check',
                    '--safebrowsing-disable-auto-update',
                    '--enable-automation',
                    '--password-store=basic',
                    '--use-mock-keychain',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-ipc-flooding-protection',
                    '--disable-software-rasterizer',
                    '--disable-canvas-aa',
                    '--disable-2d-canvas-clip-aa',
                    '--disable-gl-drawing-for-tests',
                    '--hide-scrollbars',
                    '--mute-audio',
                    // Render.com specific optimizations
                    ...(isRender ? [
                        '--single-process',
                        '--disable-audio-output',
                        '--disable-background-media-suspend',
                        '--disable-notifications',
                        '--disable-device-discovery-notifications',
                        '--virtual-time-budget=5000'
                    ] : [])
                ],
                timeout: isRender ? 120000 : 60000,  // Longer timeout for Render
                protocolTimeout: isRender ? 120000 : 60000,
                ...(isRender && {
                    pipe: true,  // Use pipe instead of websocket on Render
                    dumpio: false  // Disable debug output
                })
            }
        });

        // QR Code generation
        this.whatsappClient.on('qr', (qr) => {
            console.log('📱 QR CODE GENERATED! Scan this with your WhatsApp:');
            console.log('QR Data length:', qr.length);
            qrcode.generate(qr, { small: true });

            // Store QR code for web interface
            this.currentQRCode = qr;

            // Generate QR code as base64 image for web interface
            qrcode.toDataURL(qr, { width: 300, margin: 2 }, (err, url) => {
                if (!err) {
                    this.currentQRCodeImage = url;
                    console.log('✅ QR code image generated for web interface');
                    console.log('Image URL length:', url.length);
                    // Emit QR code image to connected clients
                    this.io.emit('qr-code-image', url);
                } else {
                    console.error('❌ Failed to generate QR code image:', err);
                }
            });

            // Emit QR code data to connected clients
            this.io.emit('qr-code', qr);
        });

        // Client ready
        this.whatsappClient.on('ready', () => {
            console.log('✅ WhatsApp client is ready!');
            this.isClientReady = true;
            this.io.emit('client-ready', true);
        });

        // Authentication success
        this.whatsappClient.on('authenticated', () => {
            console.log('🔐 WhatsApp client authenticated');
            this.io.emit('authenticated', true);
        });

        // Authentication failure
        this.whatsappClient.on('auth_failure', (msg) => {
            console.error('❌ WhatsApp authentication failed:', msg);
            this.io.emit('auth-failure', msg);
        });

        // Disconnection - handled below with crash detection

        // Loading screen
        this.whatsappClient.on('loading_screen', (percent, message) => {
            console.log(`⏳ Loading: ${percent}% - ${message}`);
        });

        // Change state
        this.whatsappClient.on('change_state', (state) => {
            console.log(`🔄 State changed to: ${state}`);
        });

        // Remote session saved
        this.whatsappClient.on('remote_session_saved', () => {
            console.log('💾 Remote session saved');
        });

        // Message received
        this.whatsappClient.on('message', async (message) => {
            await this.handleIncomingMessage(message);
        });

        // Handle Puppeteer crashes
        this.whatsappClient.on('disconnected', (reason) => {
            console.log('🔌 WhatsApp client disconnected:', reason);
            this.isClientReady = false;
            this.io.emit('disconnected', reason);
            
            // If disconnected due to crash, retry
            if (reason === 'NAVIGATION' || reason === 'CONNECTION_LOST') {
                console.log('🔄 Connection lost, will retry in 15 seconds...');
                setTimeout(() => {
                    this.retryWhatsAppConnection();
                }, 15000);
            }
        });

        // Initialize client with timeout
        console.log('🚀 Starting WhatsApp client initialization...');
        this.whatsappClient.initialize();

        // Set a timeout to detect if QR code generation fails
        setTimeout(() => {
            if (!this.currentQRCode && !this.isClientReady) {
                console.log('⚠️  No QR code generated after 30 seconds, retrying...');
                this.retryWhatsAppConnection();
            }
        }, 30000);
    }

    retryWhatsAppConnection() {
        console.log('🔄 Retrying WhatsApp connection...');
        try {
            if (this.whatsappClient) {
                console.log('🧹 Destroying existing client...');
                this.whatsappClient.destroy().catch(err => {
                    console.log('⚠️  Error destroying client (expected):', err.message);
                });
                this.whatsappClient = null;
            }
            
            // Clear current state
            this.currentQRCode = null;
            this.currentQRCodeImage = null;
            this.isClientReady = false;
            
            // Wait longer before reinitializing to allow cleanup
            console.log('⏳ Waiting 10 seconds before retry...');
            setTimeout(() => {
                console.log('🚀 Starting retry attempt...');
                this.setupWhatsApp();
            }, 10000);
        } catch (error) {
            console.error('❌ Error during retry:', error);
            // Even if there's an error, try to restart after a delay
            setTimeout(() => {
                console.log('🔄 Emergency retry after error...');
                this.setupWhatsApp();
            }, 15000);
        }
    }

    setupSocketIO() {
        this.io.on('connection', (socket) => {
            console.log('🔗 Client connected to WebSocket');

            // Send current status
            socket.emit('client-ready', this.isClientReady);

            socket.on('disconnect', () => {
                console.log('🔌 Client disconnected from WebSocket');
            });
        });
    }

    async handleIncomingMessage(message) {
        try {
            // Skip messages from self or groups for now
            if (message.fromMe || message.from.includes('@g.us')) {
                return;
            }

            // Extract message data
            const messageData = {
                from: message.from,
                body: message.body,
                timestamp: message.timestamp,
                type: message.type,
                id: message.id._serialized
            };

            console.log(`📨 Received message from ${message.from}: ${message.body}`);

            // Emit to connected clients for real-time monitoring
            this.io.emit('message-received', messageData);

            // Process message through sofIA agent
            await this.processThroughSofia(messageData);

        } catch (error) {
            console.error('Error handling incoming message:', error);
        }
    }

    async processThroughSofia(messageData) {
        try {
            console.log(`🔄 Processing message from ${messageData.from} (${messageData.id})`);
            
            // Send message to sofIA Python agent for processing
            const response = await axios.post(`${this.sofiaApiUrl}/process-whatsapp-message`, {
                user_id: messageData.from,
                message: messageData.body,
                timestamp: messageData.timestamp,
                message_id: messageData.id
            }, {
                timeout: 100000, // 100 second timeout
                headers: {
                    'Content-Type': 'application/json',
                    'X-Request-ID': messageData.id
                }
            });

            if (response.data && response.data.reply) {
                // Send response back through WhatsApp
                await this.whatsappClient.sendMessage(messageData.from, response.data.reply);

                console.log(`📤 Sent reply to ${messageData.from}: ${response.data.reply.substring(0, 100)}...`);

                // Emit reply for monitoring
                this.io.emit('message-sent', {
                    to: messageData.from,
                    message: response.data.reply,
                    timestamp: Date.now(),
                    request_id: messageData.id
                });
            } else {
                console.warn(`⚠️ No reply received for message ${messageData.id}`);
            }

        } catch (error) {
            console.error(`❌ Error processing message ${messageData.id} from ${messageData.from}:`, error.message);

            // Send error message to user with more context
            try {
                const errorMessage = error.response?.status === 429 
                    ? "I'm receiving many messages right now. Please wait a moment and try again."
                    : "Sorry, I'm having trouble processing your request right now. Please try again later.";
                    
                await this.whatsappClient.sendMessage(messageData.from, errorMessage);
                
                console.log(`📤 Sent error message to ${messageData.from}`);
            } catch (sendError) {
                console.error('Error sending error message:', sendError);
            }
        }
    }

    start(port = 3001) {
        this.server.listen(port, () => {
            console.log(`🚀 sofIA WhatsApp Bridge running on port ${port}`);
            console.log(`📱 Waiting for WhatsApp QR code...`);
        });
    }
}

// Handle uncaught Puppeteer errors
process.on('uncaughtException', (error) => {
    console.error('💥 Uncaught Exception:', error.message);
    if (error.message.includes('Protocol error') || error.message.includes('Target closed')) {
        console.log('🔄 Puppeteer crash detected, will retry...');
        // The retry mechanism will handle this
    }
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('💥 Unhandled Rejection at:', promise, 'reason:', reason);
});

// Start the bridge
const bridge = new SofiaWhatsAppBridge();
bridge.start(process.env.PORT || 3001);

module.exports = SofiaWhatsAppBridge;