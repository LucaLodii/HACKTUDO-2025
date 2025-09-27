from google.adk.agents import Agent
from .prompt import ORCHESTRATOR_AGENT_PROMPT
from .tools import process_user_message

orchestrator_agent = Agent(
    model='gemini-2.5-flash',
    name='sofIA-orchestrator',
    description=('Main conversation agent that coordinates payment flows via A2A communication'),
    instruction=(ORCHESTRATOR_AGENT_PROMPT),
    tools=[process_user_message],
)