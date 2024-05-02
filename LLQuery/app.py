import os
from src.utils import load_config
from langchain_community.llms import Ollama
from langchain_core.output_parsers import StrOutputParser
from chainlit.playground.config import add_llm_provider
from chainlit.playground.providers.langchain import LangchainGenericProvider

from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig

import chainlit as cl

cfg = load_config()

# <- Connect to LLM Model
base_url = os.getenv("OLLAMA_BASE_URL") or cfg.OLLAMA_BASE_URL

llm = Ollama(base_url=base_url, model=cfg.BASE_MODEL)
# ->

# <- DB Schema Related code
# Add the LLM provider
add_llm_provider(
    LangchainGenericProvider(
        # It is important that the id of the provider matches the _llm_type
        id=llm._llm_type,
        # The name is not important. It will be displayed in the UI.
        name=cfg.BASE_MODEL,
        # This should always be a Langchain llm instance (correctly configured)
        llm=llm,
        # If the LLM works with messages, set this to True
        is_chat=False,
    )
)


from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri(cfg.DB_DATA_PATH)

schema_query = """
SELECT 
    name, 
    sql 
FROM sqlite_master 
WHERE type = 'table' 
ORDER BY name;
"""

# You can add logic for any other db schema or connection to db
schema_response = db.run(schema_query)
# ->


@cl.on_chat_start
async def on_chat_start():
    model = llm
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"Provided this schema:\n{schema_response}\nGenerate SQL for user question only if user ask about any table that exist in this schema.",
            ),
            ("human", "{question}"),
        ]
    )
    runnable = prompt | model | StrOutputParser()
    cl.user_session.set("runnable", runnable)


@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable

    msg = cl.Message(content="")

    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await msg.stream_token(chunk)

    await msg.send()
