# Tools package for sofIA Payment Agent

from .ap2_protocol.ap2_tool import ap2_protocol_tool
from .whatsapp.whatsapp_tool import whatsapp_tool

# Only import bemobi_tool if credentials are available
try:
    import os
    if os.getenv("BEMOBI_API_KEY"):
        from .bemobi.bemobi_tool import bemobi_tool
        __all__ = ["ap2_protocol_tool", "whatsapp_tool", "bemobi_tool"]
    else:
        bemobi_tool = None
        __all__ = ["ap2_protocol_tool", "whatsapp_tool"]
except ImportError:
    bemobi_tool = None
    __all__ = ["ap2_protocol_tool", "whatsapp_tool"]
