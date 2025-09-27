from google.adk.agents import Agent
from .prompt import SOFIA_AGENT_PROMPT
from .tools import (
    ap2_protocol_tool,
    whatsapp_tool,
    bemobi_tool,
)

# Build tools list dynamically based on available tools
tools_list = [ap2_protocol_tool, whatsapp_tool]
if bemobi_tool is not None:
    tools_list.append(bemobi_tool)

root_agent = Agent(
    model='gemini-2.5-flash',
    name='sofIA',
    description=('An AI payment agent for secure WhatsApp transactions using AP2 protocol.'),
    instruction=(SOFIA_AGENT_PROMPT),
    tools=tools_list,
)
