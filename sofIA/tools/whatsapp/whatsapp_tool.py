"""
WhatsApp Tool for sofIA Payment Agent

This tool provides WhatsApp Web.js functionality through a Node.js bridge.
"""

import os
from typing import Dict, Any, Optional
import requests
import asyncio
import aiohttp


class WhatsAppTool:
    """Tool for handling WhatsApp Web.js operations through Node.js bridge."""

    def __init__(self):
        self.name = "whatsapp"
        self.description = "Send messages via WhatsApp Web.js bridge and handle user interactions"
        self.parameters = {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["send_message", "get_client_info", "check_status"],
                    "description": "The WhatsApp operation to perform"
                },
                "to": {
                    "type": "string",
                    "description": "Recipient phone number (with country code, no +)"
                },
                "message": {
                    "type": "string",
                    "description": "Message text to send"
                }
            },
            "required": ["operation"]
        }

        # WhatsApp Bridge configuration
        self.bridge_url = os.getenv("WHATSAPP_BRIDGE_URL", "http://localhost:3001")
        self.bridge_timeout = 10  # seconds
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute WhatsApp operation."""
        operation = kwargs.get("operation")

        try:
            if operation == "send_message":
                return await self._send_message(**kwargs)
            elif operation == "get_client_info":
                return await self._get_client_info(**kwargs)
            elif operation == "check_status":
                return await self._check_status(**kwargs)
            else:
                return {"error": f"Unknown operation: {operation}"}

        except Exception as e:
            return {"error": f"WhatsApp operation failed: {str(e)}"}
    
    async def _send_message(self, to: str, message: str, **kwargs) -> Dict[str, Any]:
        """Send a text message via WhatsApp Web.js bridge."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "to": to,
                    "message": message
                }

                async with session.post(
                    f"{self.bridge_url}/send-message",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.bridge_timeout)
                ) as response:
                    response_data = await response.json()

                    if response.status == 200:
                        return {
                            "success": True,
                            "recipient": to,
                            "message": message,
                            "bridge_response": response_data
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Bridge error: {response_data.get('error', 'Unknown error')}"
                        }

        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": f"Failed to communicate with WhatsApp bridge: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to send WhatsApp message: {str(e)}"
            }
    
    async def _get_client_info(self, **kwargs) -> Dict[str, Any]:
        """Get WhatsApp client information from bridge."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.bridge_url}/client-info",
                    timeout=aiohttp.ClientTimeout(total=self.bridge_timeout)
                ) as response:
                    response_data = await response.json()

                    if response.status == 200:
                        return {
                            "success": True,
                            "client_info": response_data.get("client_info"),
                            "bridge_url": self.bridge_url
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Bridge error: {response_data.get('error', 'Unknown error')}"
                        }

        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": f"Failed to communicate with WhatsApp bridge: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get client info: {str(e)}"
            }

    async def _check_status(self, **kwargs) -> Dict[str, Any]:
        """Check WhatsApp bridge status."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.bridge_url}/health",
                    timeout=aiohttp.ClientTimeout(total=self.bridge_timeout)
                ) as response:
                    response_data = await response.json()

                    if response.status == 200:
                        return {
                            "success": True,
                            "bridge_status": response_data,
                            "bridge_url": self.bridge_url
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Bridge health check failed: {response.status}"
                        }

        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": f"Failed to communicate with WhatsApp bridge: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to check bridge status: {str(e)}"
            }


# Initialize tool instance
_whatsapp_tool = WhatsAppTool()


def whatsapp_tool(**kwargs):
    """WhatsApp tool function."""
    return _whatsapp_tool.execute(**kwargs)
