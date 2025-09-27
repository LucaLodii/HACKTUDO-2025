# WhatsApp Web.js Setup Guide for sofIA

This guide shows how to set up WhatsApp integration using WhatsApp Web.js instead of the Cloud API.

## 🚀 **Why WhatsApp Web.js?**

Perfect for hackathons because:
- ✅ No API approval needed (works immediately)
- ✅ Uses your personal WhatsApp account
- ✅ QR code setup (scan with your phone)
- ✅ Real-time messaging
- ✅ No business verification required

## 📋 **Prerequisites**

- Node.js 16+ installed
- Python 3.12+
- Personal WhatsApp account
- Chrome/Chromium browser

## 🛠️ **Setup Instructions**

### 1. **Install Node.js Dependencies**

```bash
cd whatsapp-bridge
npm install
```

### 2. **Start the WhatsApp Bridge**

```bash
# Terminal 1: Start the WhatsApp bridge
cd whatsapp-bridge
npm start
```

You'll see:
```
🚀 sofIA WhatsApp Bridge running on port 3001
📱 Waiting for WhatsApp QR code...
```

### 3. **Scan QR Code**

1. A QR code will appear in your terminal
2. Open WhatsApp on your phone
3. Go to Settings > Linked Devices > Link a Device
4. Scan the QR code

You'll see:
```
✅ WhatsApp client is ready!
```

### 4. **Start the Python sofIA Agent**

```bash
# Terminal 2: Start the sofIA agent
uv run app.py
```

You'll see:
```
🚀 Starting sofIA WhatsApp Payment Agent...
📱 AP2 Protocol Implementation for Secure Payments
```

## 📱 **Testing the Integration**

### 1. **Send a test message to your WhatsApp**

From any contact, send a message to the phone number you used for the QR code.

### 2. **Expected Flow:**

```
You: "Hello sofIA"
sofIA: "Hi! I received your message: 'Hello sofIA'. I'm sofIA, your AI payment assistant..."

You: "I want to buy coffee"
sofIA: [Creates AP2 Intent Mandate and starts payment flow]
```

## 🔧 **Configuration**

### Environment Variables

Create `.env` file:
```bash
# WhatsApp Bridge
WHATSAPP_BRIDGE_URL=http://localhost:3001

# sofIA Agent
SOFIA_API_URL=http://localhost:8000

# Optional: For production
HOST=0.0.0.0
PORT=8000
```

### Bridge Configuration

In `whatsapp-bridge/server.js`, you can modify:
```javascript
// Port for the bridge
const port = process.env.PORT || 3001;

// sofIA API URL
const sofiaApiUrl = process.env.SOFIA_API_URL || 'http://localhost:8000';
```

## 🎭 **Demo Mode (Without WhatsApp)**

If you want to test AP2 protocol without WhatsApp:

```bash
uv run app.py demo
```

This runs a complete AP2 payment flow simulation.

## 🔍 **Monitoring & Debugging**

### 1. **Check Bridge Health**
```bash
curl http://localhost:3001/health
```

### 2. **Check sofIA Agent Health**
```bash
curl http://localhost:8000/health
```

### 3. **Monitor Real-time Messages**

The bridge logs all messages:
```
📨 Received message from 5511999999999@c.us: Hello sofIA
📤 Sent reply to 5511999999999@c.us: Hi! I received your message...
```

## 🚨 **Troubleshooting**

### **QR Code Not Appearing**
```bash
# Kill and restart the bridge
pkill -f "node server.js"
cd whatsapp-bridge && npm start
```

### **Bridge Connection Failed**
```bash
# Check if bridge is running
curl http://localhost:3001/health

# Check sofIA logs for connection errors
```

### **WhatsApp Session Expired**
1. Restart the bridge
2. Scan QR code again
3. WhatsApp sessions last ~2 weeks

### **Messages Not Processing**
1. Check both services are running
2. Verify the bridge URL in environment
3. Check logs for error messages

## 📊 **Architecture**

```
Your Phone (WhatsApp) ←→ WhatsApp Web.js ←→ Node.js Bridge ←→ Python sofIA Agent
                                                                        ↓
                                                               AP2 Protocol Processing
                                                                        ↓
                                                               Bemobi Payment Gateway
```

## 🌟 **Production Considerations**

For production deployment:
1. **Use PM2** for Node.js process management
2. **Add authentication** to bridge endpoints
3. **Implement session persistence** (Redis)
4. **Set up monitoring** (health checks)
5. **Use HTTPS** for all communications

## 📞 **Support**

If you encounter issues:
1. Check the terminal logs
2. Verify QR code scanning
3. Test with `/health` endpoints
4. Ensure both services are running on correct ports

**Happy hacking! 🚀**