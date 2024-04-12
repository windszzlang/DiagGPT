import openai

from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate

from .prompt import PROMPT_TEMPLATE



class UserGPT:

    def __init__(self, topic, task_name, user_role):
        self.topic = topic
        self.task_name = task_name
        self.user_role = user_role
        self.model_name = 'gpt-4-0613'
        self.memory_model_name = 'gpt-3.5-turbo-0613'

        self.user_greeting = 'Hi, I come here to do ' + self.task_name + '. Can you help me with this task?'
        self.chat_model = self._init_chat_model(self.user_greeting)


    def _init_chat_model(self, user_greeting):
        llm = ChatOpenAI(model_name=self.model_name, streaming=True, temperature=0)
        template = PROMPT_TEMPLATE

        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt])
        memory = ConversationSummaryBufferMemory(max_token_limit=2000, input_key='input_message',
                                                 memory_key='chat_history',
                                                 return_messages=True,
                                                 human_prefix='User',
                                                 ai_prefix='AI',
                                                 llm=ChatOpenAI(temperature=0, model_name=self.memory_model_name))
        memory.save_context({'input_message': 'Hi'}, {'output': user_greeting})
        
        chat_model = LLMChain(llm=llm, prompt=chat_prompt, memory=memory)
        return chat_model

  
    def chat(self, input_message):
        output_message = self.chat_model.predict(input_message=input_message,
                                         topic=self.topic,
                                         task_name=self.task_name,
                                         user_role=self.user_role)
        return output_message