"""
sofIA WhatsApp Payment Agent - Simple Version
"""

import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Create FastAPI app
app = FastAPI(title="sofIA WhatsApp Payment Agent", version="1.0.0")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "sofIA WhatsApp Payment Agent is running!",
        "status": "success",
        "service": "sofIA",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "sofIA WhatsApp Payment Agent",
        "ap2_ready": True
    }

@app.post("/process-whatsapp-message")
async def process_whatsapp_message(request: dict):
    """Process WhatsApp messages - simple version."""
    try:
        user_id = request.get("user_id", "unknown")
        message = request.get("message", "")
        
        # Simple response logic
        if "hello" in message.lower() or "hi" in message.lower():
            reply = "Hello! I'm sofIA, your AI payment assistant. How can I help you today?"
        elif "buy" in message.lower() or "purchase" in message.lower():
            reply = "I'd be happy to help you with a purchase! What would you like to buy?"
        elif "coffee" in message.lower():
            reply = "Great choice! I can help you buy coffee. Would you like to proceed with the payment?"
        else:
            reply = "I'm here to help with your payment needs. What can I do for you?"
        
        return JSONResponse(content={
            "reply": reply,
            "user_id": user_id,
            "status": "success"
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Processing failed: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
