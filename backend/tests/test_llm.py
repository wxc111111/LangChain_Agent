import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

llm = ChatOpenAI(
    model="qwen-plus",
    api_key="",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.7,
)

response = llm.invoke([
    SystemMessage(content="你是一个专业的 Java 和 Python 技术助手。"),
    HumanMessage(content="用一句话介绍一下 LangChain。")
])

print(response.content)