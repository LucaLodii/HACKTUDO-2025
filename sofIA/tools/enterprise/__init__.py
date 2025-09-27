"""
Enterprise Tools for sofIA Agent

Provides access to enterprise-grade infrastructure components including
authentication, agent registry, verifiable credentials, and dispute resolution.
"""

# Enterprise Tools - Only import if dependencies are available
try:
    from .auth_tool import auth_tool
    from .registry_tool import registry_tool
    from .credentials_tool import credentials_tool
    from .disputes_tool import disputes_tool

    __all__ = [
        "auth_tool",
        "registry_tool",
        "credentials_tool",
        "disputes_tool"
    ]
except ImportError as e:
    # Graceful fallback if enterprise dependencies are not available
    auth_tool = None
    registry_tool = None
    credentials_tool = None
    disputes_tool = None

    __all__ = []