import openai

from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate

from .prompt import PROMPT_TEMPLATE



class ChatGPT:

    def __init__(self, topic, task_name, overview, goal, checklist, model_name='gpt-4'):
        self.topic = topic
        self.task_name = task_name
        self.overview = overview
        self.goal = goal
        self.checklist = checklist
        self.model_name = model_name
        self.memory_model_name = 'gpt-3.5-turbo'

        self.chat_model = self._init_chat_model()


    def _init_chat_model(self):
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
        
        chat_model = LLMChain(llm=llm, prompt=chat_prompt, memory=memory)
        return chat_model

  
    def chat(self, input_message):
        checklist = '; '.join(self.checklist)
        output_message = self.chat_model.predict(input_message=input_message,
                                        topic=self.topic,
                                        task_name=self.task_name,
                                        overview=self.overview,
                                        goal=self.goal,
                                        checklist=checklist)
        return output_message