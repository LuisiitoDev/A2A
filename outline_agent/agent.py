import os

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import Agent, MessageRole, ListSortOrder
from azure.identity import DefaultAzureCredential

class OutlineAgent:

    def __init__(self):
        self.client = AgentsClient(
            endpoint=os.environ['PROJECT_ENDPOINT'],
            credential=DefaultAzureCredential(
                exclude_environment_credential=True,
                exclude_managed_identity_credential=True
            )
        )

        self.agent: Agent | None = None
    
    async def create_agent(self) -> Agent:
        if self.agent:
            return self.agent
        

        self.agent = self.client.create_agent(
            model=os.environ['MODEL'],
            name='ms-foundry-outline-agent',
            instructions="""
            You are a helpful writing assistant.
            Based on the provided title or topic, write a concise outline with 4 to 6 key sections.
            Each section should be 5 to 10 words long, suitable for structuring a short blog post.
            """,
        )

        return self.agent
    
    async def run_conversation(self, user_message: str) -> list[str]:
        if not self.agent:
            await self.create_agent()
        
        thread = self.client.threads.create()

        self.client.messages.create(thread_id=thread, role=MessageRole.USER, content=user_message)
        run = self.client.runs.create_and_process(thread_id=thread, agent_id=self.agent.id)

        if run.status == 'failed':
            print(f'Title Agent: Run failed - {run.last_error}')
            return [f'Error: {run.last_error}']
        
        messages = self.client.messages.list(thread_id=thread, order=ListSortOrder.DESCENDING)
        responses = []

        for msg in messages:
            if msg.role == 'assistant' and msg.text_messages:
                for text_msg in msg.text_messages:
                    responses.append(text_msg.text.value)
                break

        return responses if responses else ['No response received']


async def create_foundry_outline_agent() -> OutlineAgent:
    agent = OutlineAgent()
    await agent.create_agent()
    return agent
