"""
BEMOBI Factory - Configurable BEMOBI Implementation

This module provides a factory pattern to switch between real BEMOBI API
and mock implementation based on environment configuration.
"""

import os
from typing import Dict, Any, Optional
from .bemobi_tool import BemobiTool
from .mock_bemobi import MockBemobiTool


class BemobiFactory:
    """Factory for creating BEMOBI tool instances"""
    
    @staticmethod
    def create_bemobi_tool() -> Optional[object]:
        """
        Create BEMOBI tool instance based on environment configuration
        
        Returns:
            BemobiTool or MockBemobiTool instance, or None if disabled
        """
        # Check if BEMOBI is enabled
        bemobi_enabled = os.getenv("BEMOBI_ENABLED", "true").lower() == "true"
        if not bemobi_enabled:
            print("🔧 BEMOBI integration disabled")
            return None
        
        # Check if we should use mock mode
        mock_mode = os.getenv("BEMOBI_MOCK_MODE", "true").lower() == "true"
        
        if mock_mode:
            print("🔧 Using Mock BEMOBI implementation for hackathon demo")
            return MockBemobiTool()
        else:
            # Check if we have real API credentials
            api_key = os.getenv("BEMOBI_API_KEY")
            secret_key = os.getenv("BEMOBI_SECRET_KEY")
            
            if not api_key or not secret_key:
                print("⚠️  Real BEMOBI API credentials not found, falling back to mock mode")
                return MockBemobiTool()
            
            print("🔧 Using Real BEMOBI API implementation")
            return BemobiTool()
    
    @staticmethod
    def get_bemobi_config() -> Dict[str, Any]:
        """
        Get BEMOBI configuration from environment variables
        
        Returns:
            Dictionary with BEMOBI configuration
        """
        return {
            "enabled": os.getenv("BEMOBI_ENABLED", "true").lower() == "true",
            "mock_mode": os.getenv("BEMOBI_MOCK_MODE", "true").lower() == "true",
            "api_key": os.getenv("BEMOBI_API_KEY"),
            "secret_key": os.getenv("BEMOBI_SECRET_KEY"),
            "base_url": os.getenv("BEMOBI_BASE_URL", "https://api.bemobi.com/v1"),
            "region": os.getenv("BEMOBI_REGION", "latam"),
            "webhook_base_url": os.getenv("WEBHOOK_BASE_URL"),
            "mock_delay": float(os.getenv("BEMOBI_MOCK_DELAY", "0.5")),
            "mock_failure_rate": float(os.getenv("BEMOBI_MOCK_FAILURE_RATE", "0.05"))
        }
    
    @staticmethod
    def print_bemobi_status():
        """Print current BEMOBI configuration status"""
        config = BemobiFactory.get_bemobi_config()
        
        print("=" * 50)
        print("🏦 BEMOBI Integration Status")
        print("=" * 50)
        print(f"Enabled: {'✅' if config['enabled'] else '❌'}")
        print(f"Mode: {'🔧 Mock' if config['mock_mode'] else '🌐 Real API'}")
        print(f"Region: {config['region'].upper()}")
        print(f"Base URL: {config['base_url']}")
        
        if config['mock_mode']:
            print(f"Mock Delay: {config['mock_delay']}s")
            print(f"Mock Failure Rate: {config['mock_failure_rate']*100:.1f}%")
        else:
            print(f"API Key: {'✅ Set' if config['api_key'] else '❌ Missing'}")
            print(f"Secret Key: {'✅ Set' if config['secret_key'] else '❌ Missing'}")
        
        print("=" * 50)


# Create the BEMOBI tool instance
bemobi_tool = BemobiFactory.create_bemobi_tool()

# Export the tool function
def get_bemobi_tool():
    """Get the configured BEMOBI tool instance"""
    return bemobi_tool

def get_bemobi_tool_function():
    """Get the BEMOBI tool function for agent integration"""
    if bemobi_tool is None:
        return None
    
    # Return the appropriate execute function based on tool type
    if hasattr(bemobi_tool, 'execute'):
        return bemobi_tool.execute
    else:
        return None
