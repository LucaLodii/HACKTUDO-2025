# Bemobi payment gateway integration for sofIA

from .bemobi_factory import bemobi_tool, get_bemobi_tool_function

# Export the tool function for agent integration
def get_bemobi_tool():
    """Get the configured BEMOBI tool function"""
    return get_bemobi_tool_function()