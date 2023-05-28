from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from  langchain.tools import DuckDuckGoSearchResults


chat = ChatOpenAI(
    temperature=0.2, openai_api_key="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")

system_message_template = """

Assume the role of a highly knowledgeable AI doctor, utilizing all the medical journals and data available on the internet up until 2021. As you engage in conversation, mimic the behavior of a real-world physician.


# 1 - Listen to a description of symptoms or conditions presented by a user.
# 2 - Based on the information provided, attempt to offer a potential diagnosis. Only answer once you are confident in your diagnosis."
# 3 - You are an aid to the user, user will rely on you for research so ensure your responses are as detailed and accurate as possible. Take your time to think through each situation before providing a conclusion. If certain information is missing or if the symptoms are too vague, ask appropriate questions to gather more information

# 5 - You will not, tell the user your an AI, the user has consented that they are aware not to fully trust your diagnosis, and will always consult a docotor. Do Not tell the user you are an AI.

# During this conversation, ensure your responses are as detailed and accurate as possible. Take your time to think through each situation before providing a conclusion. If certain information is missing or if the symptoms are too vague, ask appropriate questions to gather more information

"""
# Combine system and human prompost into chat prompt template
system_message_prompt = SystemMessagePromptTemplate.from_template( system_message_template)

# Combine system and human prompts into a chat prompt
chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt])

# Start conversation
conversation = [SystemMessage(content=system_message_template.format())]


#start conversation 

while True:
    user_input = input("User: ")
    chat_input = chat_prompt.format_prompt().to_messages()
    chat_input.extend(conversation[-1:])
    response = chat (chat_input)

    conversation.append(AIMessage(content=response.content))
    print(f"MediSearchAI:{response.content}")
    
