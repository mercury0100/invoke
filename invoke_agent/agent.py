from typing import Optional, List, Union, Dict
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

from invoke_agent.core import api_executor
from invoke_agent.context import build_context, DEFAULT_CONTEXT


class InvokeAgent:
    def __init__(
        self,
        llm: BaseChatModel,
        agents: Optional[Union[str, List[Union[str, Dict[str, str]]]]] = None,
        tools: Optional[List[BaseTool]] = None,
        context: Optional[str] = None,
        verbose: bool = False,
    ):
        self.llm = llm
        self.tools = tools or [api_executor]
        # Use provided context or DEFAULT_CONTEXT
        base_prompt = context if context is not None else DEFAULT_CONTEXT
        # Build system prompt with optional agents map
        self.system_prompt = build_context(base_prompt=base_prompt, agents=agents)
        self.chat_history = [SystemMessage(content=self.system_prompt)]

        prompt = ChatPromptTemplate.from_messages([
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        self.agent = create_tool_calling_agent(llm=self.llm, tools=self.tools, prompt=prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=verbose)

    def chat(self, user_input: str) -> str:
        self.chat_history.append(HumanMessage(content=user_input))

        result = self.executor.invoke({
            "input": user_input,
            "chat_history": self.chat_history
        })

        response = result.get("output")
        self.chat_history.append(AIMessage(content=response))
        return response
