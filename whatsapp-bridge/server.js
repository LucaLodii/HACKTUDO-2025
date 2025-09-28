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

            // Emit QR code to connected clients
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