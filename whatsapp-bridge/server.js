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
                service: 'sofIA WhatsApp Bridge'
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

        // QR Code web interface
        this.app.get('/qr', (req, res) => {
            res.send(`
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>sofIA WhatsApp Bridge - QR Code</title>
                    <style>
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            margin: 0;
                            padding: 20px;
                            min-height: 100vh;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        }
                        .container {
                            background: white;
                            border-radius: 20px;
                            padding: 40px;
                            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                            text-align: center;
                            max-width: 500px;
                            width: 100%;
                        }
                        .logo {
                            font-size: 2.5em;
                            font-weight: bold;
                            color: #667eea;
                            margin-bottom: 10px;
                        }
                        .subtitle {
                            color: #666;
                            margin-bottom: 30px;
                        }
                        .qr-container {
                            background: #f8f9fa;
                            border-radius: 15px;
                            padding: 30px;
                            margin: 20px 0;
                        }
                        .qr-code {
                            display: inline-block;
                            background: white;
                            padding: 20px;
                            border-radius: 10px;
                            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                        }
                        .status {
                            margin: 20px 0;
                            padding: 15px;
                            border-radius: 10px;
                            font-weight: 500;
                        }
                        .status.waiting {
                            background: #fff3cd;
                            color: #856404;
                            border: 1px solid #ffeaa7;
                        }
                        .status.ready {
                            background: #d4edda;
                            color: #155724;
                            border: 1px solid #c3e6cb;
                        }
                        .instructions {
                            background: #e3f2fd;
                            padding: 20px;
                            border-radius: 10px;
                            margin: 20px 0;
                            text-align: left;
                        }
                        .instructions ol {
                            margin: 10px 0;
                            padding-left: 20px;
                        }
                        .instructions li {
                            margin: 8px 0;
                            color: #1976d2;
                        }
                        .refresh-btn {
                            background: #667eea;
                            color: white;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 25px;
                            cursor: pointer;
                            font-size: 16px;
                            margin: 10px;
                            transition: background 0.3s;
                        }
                        .refresh-btn:hover {
                            background: #5a6fd8;
                        }
                        .auto-refresh {
                            color: #666;
                            font-size: 14px;
                            margin-top: 20px;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="logo">sofIA</div>
                        <div class="subtitle">WhatsApp Payment Agent Bridge</div>
                        
                        <div id="status" class="status waiting">
                            ${this.isClientReady ? '✅ WhatsApp Connected' : '⏳ Waiting for QR Code...'}
                        </div>
                        
                        <div class="qr-container">
                            <div id="qr-code" class="qr-code">
                                ${this.currentQRCodeImage ? 
                                    `<img src="${this.currentQRCodeImage}" alt="QR Code" style="max-width: 300px;">` :
                                    '<p>Generating QR Code...</p>'
                                }
                            </div>
                        </div>
                        
                        <div class="instructions">
                            <h3>📱 How to Connect:</h3>
                            <ol>
                                <li>Open WhatsApp on your phone</li>
                                <li>Tap the three dots menu (⋮)</li>
                                <li>Select "Linked Devices"</li>
                                <li>Tap "Link a Device"</li>
                                <li>Scan the QR code above</li>
                            </ol>
                        </div>
                        
                        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Page</button>
                        
                        <div class="auto-refresh">
                            This page auto-refreshes every 5 seconds
                        </div>
                    </div>
                    
                    <script src="/socket.io/socket.io.js"></script>
                    <script>
                        // Auto-refresh every 10 seconds
                        setInterval(() => {
                            location.reload();
                        }, 10000);
                        
                        // Function to display QR code image
                        function displayQRCode(qrImageUrl) {
                            const qrCode = document.getElementById('qr-code');
                            if (qrCode) {
                                qrCode.innerHTML = \`<img src="\${qrImageUrl}" alt="QR Code" style="max-width: 300px;">\`;
                            }
                        }
                        
                        // WebSocket connection for real-time updates
                        let socket;
                        try {
                            socket = io();
                            
                            socket.on('qr-code-image', (qrImageUrl) => {
                                displayQRCode(qrImageUrl);
                                document.getElementById('status').innerHTML = '⏳ Scan QR Code with WhatsApp';
                                document.getElementById('status').className = 'status waiting';
                            });
                            
                            socket.on('client-ready', (ready) => {
                                if (ready) {
                                    document.getElementById('status').innerHTML = '✅ WhatsApp Connected';
                                    document.getElementById('status').className = 'status ready';
                                    document.getElementById('qr-code').innerHTML = '<p>✅ Connected Successfully!</p>';
                                }
                            });
                            
                            socket.on('auth-failure', (msg) => {
                                document.getElementById('status').innerHTML = '❌ Authentication Failed: ' + msg;
                                document.getElementById('status').className = 'status waiting';
                            });
                            
                        } catch (error) {
                            console.log('WebSocket not available, using fallback mode');
                            // Fallback: try to get QR code via API
                            fetch('/qr-image')
                                .then(response => response.blob())
                                .then(blob => {
                                    const url = URL.createObjectURL(blob);
                                    const qrDisplay = document.getElementById('qr-display');
                                    if (qrDisplay) {
                                        qrDisplay.innerHTML = \`<img src="\${url}" alt="QR Code" style="max-width: 300px;">\`;
                                    }
                                })
                                .catch(err => console.log('QR image not available yet'));
                        }
                        
                        // Initial QR code display if available
                        ${this.currentQRCodeImage ? `displayQRCode('${this.currentQRCodeImage}');` : ''}
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
        // Initialize WhatsApp client with local authentication
        this.whatsappClient = new Client({
            authStrategy: new LocalAuth({
                clientId: "sofia-payment-agent"
            }),
            puppeteer: {
                headless: true,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu'
                ]
            }
        });

        // QR Code generation
        this.whatsappClient.on('qr', (qr) => {
            console.log('📱 Scan this QR code with your WhatsApp:');
            qrcode.generate(qr, { small: true });

            // Store QR code for web interface
            this.currentQRCode = qr;

            // Generate QR code as base64 image for web interface
            qrcode.toDataURL(qr, { width: 300, margin: 2 }, (err, url) => {
                if (!err) {
                    this.currentQRCodeImage = url;
                    // Emit QR code image to connected clients
                    this.io.emit('qr-code-image', url);
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

        // Disconnection
        this.whatsappClient.on('disconnected', (reason) => {
            console.log('🔌 WhatsApp client disconnected:', reason);
            this.isClientReady = false;
            this.io.emit('disconnected', reason);
        });

        // Message received
        this.whatsappClient.on('message', async (message) => {
            await this.handleIncomingMessage(message);
        });

        // Initialize client
        this.whatsappClient.initialize();
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

// Start the bridge
const bridge = new SofiaWhatsAppBridge();
bridge.start(process.env.PORT || 3001);

module.exports = SofiaWhatsAppBridge;