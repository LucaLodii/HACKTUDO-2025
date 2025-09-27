# Tools package for sofIA Payment Agent

from .ap2_protocol.ap2_tool import ap2_protocol_tool
from .whatsapp.whatsapp_tool import whatsapp_tool

# Only import bemobi_tool if credentials are available
try:
    import os
    if os.getenv("BEMOBI_API_KEY"):
        from .bemobi.bemobi_tool import bemobi_tool
    else:
        bemobi_tool = None
except ImportError:
    bemobi_tool = None

# Import enterprise tools if available
try:
    from .enterprise import auth_tool, registry_tool, credentials_tool, disputes_tool
    enterprise_tools = [auth_tool, registry_tool, credentials_tool, disputes_tool]
    enterprise_tools = [tool for tool in enterprise_tools if tool is not None]
except ImportError:
    enterprise_tools = []

# Build the tools list
base_tools = ["ap2_protocol_tool", "whatsapp_tool"]
if bemobi_tool is not None:
    base_tools.append("bemobi_tool")

# Add enterprise tools to exports
enterprise_tool_names = [tool.name if tool else None for tool in enterprise_tools]
enterprise_tool_names = [name for name in enterprise_tool_names if name]

__all__ = base_tools + enterprise_tool_names
