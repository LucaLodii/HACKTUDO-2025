from google.adk.agents import Agent
from .prompt import SOFIA_AGENT_PROMPT
from .tools import (
    ap2_protocol_tool,
    whatsapp_tool,
    bemobi_tool,
)
# Import subscription management tools
from .tools.subscription_management import subscription_management_tool
from .tools.renewal_orchestration import renewal_orchestration_tool
from .tools.plan_management import plan_management_tool

# Import enterprise tools if available
try:
    from .tools.enterprise import auth_tool, registry_tool, credentials_tool, disputes_tool
    enterprise_tools = [auth_tool, registry_tool, credentials_tool, disputes_tool]
    enterprise_tools = [tool for tool in enterprise_tools if tool is not None]
except ImportError:
    enterprise_tools = []

# Build tools list dynamically based on available tools
tools_list = [ap2_protocol_tool, whatsapp_tool]
if bemobi_tool is not None:
    tools_list.append(bemobi_tool)

# Add subscription management tools
tools_list.extend([
    subscription_management_tool,
    renewal_orchestration_tool,
    plan_management_tool
])

# Add enterprise tools if available
tools_list.extend(enterprise_tools)

root_agent = Agent(
    model='gemini-2.5-flash',
    name='sofIA',
    description=('An AI subscription management and payment agent for secure WhatsApp transactions using AP2 protocol.'),
    instruction=(SOFIA_AGENT_PROMPT),
    tools=tools_list,
)
