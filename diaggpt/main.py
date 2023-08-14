import os
import logging
import re
from queue import Queue
from typing import List, Dict, Tuple
# import openai

from langchain.chat_models import ChatOpenAI
from langchain import LLMChain, PromptTemplate
from langchain import SerpAPIWrapper
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.docstore.document import Document
from langchain.memory import ConversationSummaryBufferMemory, ReadOnlySharedMemory
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate

from opensearchpy import NotFoundError

from .embedding.embeder import Embedder
from .prompts import CHAT_PROMPT_TEMPLATE, ENRICH_TOPIC_PROMPT, MANAGE_TOPIC_PROMPT, USER_INTRO, AI_INTRO
from .tasks import load_predefined_tasks


logging.basicConfig(level=getattr(logging, os.environ.get('LOG_LEVEL', 'INFO')))



class StreamingQueueCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.q = Queue(10)

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.q.put(token)

    def on_llm_end(self, response, **kwargs) -> None:
        self.q.put(None)

def tool(name, description):
    def decorator(func):
        func.name = name
        func.description = description
        return func
    return decorator


class DiagGPT():

    predefined_tasks = load_predefined_tasks()

    def __init__(self, embedder: Embedder=None):
        """Initializes the MainQAChain.

        Args:
            embedder: An instance of Embedder. Should be the general background knowledge.
        """
        self.background_embedder = embedder
        streaming_callback = StreamingQueueCallbackHandler()
        # if streaming_callbacks is None:
            # streaming_callbacks = [StreamingStdOutCallbackHandler()]
        self.streaming_buffer = streaming_callback.q
        
        self.gpt4 = 'gpt-4' # 'gpt-4-0613'
        # gpt4 is slow and summary will block other process
        self.gpt3 = 'gpt-3.5-turbo' # 'gpt-3.5-turbo-0613'

        self.topic_stack = []
        self.tool_list = [self.stay_at_the_current_topic,
                          self.create_a_new_topic,
                          self.finish_the_current_topic,
                          self.finish_the_current_topic_and_create_a_new_topic_together,
                          self.finish_the_current_topic_and_jump_to_an_existing_topic_together,
                          self.jump_to_an_existing_topic,
                          self.load_topics_from_a_predefined_task]

        self.chat_model = self._init_chat_model([streaming_callback])
        self.topic_enricher = self._init_topic_enricher(self.chat_model.memory)
        self.topic_manage_agent = self._init_topic_manage_agent(self.chat_model.memory)

        self.beginning_topic = self.introduction_topic = 'Introduce yourself to user'
        self.topic_type = {
            'ask': 'Ask user: ',
            'answer': 'Answer user: ',
            'goal': 'Complete goal: '
        }
        self.current_task = {}

        self.init_topics()

    def _init_chat_model(self, callbacks) -> LLMChain:
        """Initializes the chat model.

        Args:
            callbacks: A list of async callback handlers.

        Returns:
            The chat model.
        """
        llm = ChatOpenAI(model_name=self.gpt4, streaming=True, callbacks=callbacks,
                          temperature=0)
        template = CHAT_PROMPT_TEMPLATE

        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt])
        memory = ConversationSummaryBufferMemory(max_token_limit=2000, input_key='human_input',
                                                 memory_key="chat_history",
                                                 return_messages=True,
                                                 human_prefix='User',
                                                 ai_prefix='AI (Medical Expert)', # Legal or Medical
                                                 llm=ChatOpenAI(temperature=0, model_name=self.gpt3))
        memory.save_context({'human_input': USER_INTRO}, {'output': AI_INTRO})
        
        chat_model = LLMChain(llm=llm, prompt=chat_prompt, memory=memory)
        return chat_model

    def _init_topic_enricher(self, memory) -> LLMChain:
        llm = ChatOpenAI(model_name=self.gpt4, temperature=0)
        prompt = PromptTemplate(input_variables=['original_topic', 'chat_history'], template=ENRICH_TOPIC_PROMPT)
        chain = LLMChain(llm=llm, prompt=prompt, memory=ReadOnlySharedMemory(memory=memory))
        return chain
    
    def _init_topic_manage_agent(self, memory) -> LLMChain:
        llm = ChatOpenAI(model_name=self.gpt4, temperature=0)
        prompt = PromptTemplate(input_variables=['topic_list', 'current_topic', 'tool_description', 'tool_names', 'human_input', 'chat_history'], template=MANAGE_TOPIC_PROMPT)
        chain = LLMChain(llm=llm, prompt=prompt, memory=ReadOnlySharedMemory(memory=memory))
        return chain

    @tool(
        name='Stay At the Current Topic',
        description='useful when you think the user still want to stay at the current topic and will talk more about this topic.'
                    'This tool does not have any input.'
    )
    def stay_at_the_current_topic(self):
        return self.topic_stack[-1]

    @tool(
        name='Create a New Topic',
        description='useful when you think the user starts a new topic which is different from the current topic, and will discuss this topic next.'
                    'If you want to create a new topic, but the new topic is similar to the current topic, please do not use this tool and use the tool: Stay At the Current Topic'
                    'If you want to create a new topic, but the new topic is similar to an existing topic on the topic list , please do not use this tool and use the tool: Jump To Another Topic'
                    'The input to this tool should be a string representing the name of the new topic.'
    )
    def create_a_new_topic(self, topic_name: str):
        topic_name = self.topic_type['answer'] + topic_name
        self.topic_stack.append(topic_name)
        return topic_name

    @tool(
        name='Finish the Current Topic',
        description='useful when you think the user has already known about the answer of current topic and wants to finish the current topic,'
                    'or the user has already answered the question you ask in the current topic.'
                    'or the user does not want to talk more about the current topic and wants to finish it'
                    'This tool does not have any input.'
    )
    def finish_the_current_topic(self):
        if self.topic_stack[-1] == self.beginning_topic:
            self.final_goal = 'None'
            return None
        elif len(self.topic_stack) > 1:
            return self.topic_stack.pop()
        else:
            return None
        
    @tool(
        name='Finish the Current Topic and Create a New topic Together',
        description='useful when you think the user want to finish the current topic and create a new topic in one round of dialogue'
                    'If you want to create a new topic, but the new topic is similar to an existing topic on the topic list , please do not use this tool'
                    'The input to this tool should be a string representing the name of the new created topic.'
    )
    def finish_the_current_topic_and_create_a_new_topic_together(self, topic_name: str):
        self.finish_the_current_topic()
        self.create_a_new_topic(topic_name)
        return topic_name
    
    @tool(
        name='Finish the Current Topic and Jump To an Existing Topic Together',
        description='useful when you think the user want to finish the current topic and jump to an exisiting topic in one round of dialogue'
                    'The input to this tool should be a string representing the name of an existing topic in the topic list, which must be one topic from the topic list'
    )
    def finish_the_current_topic_and_jump_to_an_existing_topic_together(self, topic_name: str):
        self.finish_the_current_topic()
        self.jump_to_an_existing_topic(topic_name)
        return topic_name

    @tool(
        name='Jump To an Existing Topic',
        description='useful when you think the user wants to jump to an exisiting topic (recall a previous topic) whic is in the topic list.'
                    'The input to this tool should be a string representing the name of an existing topic in the topic list, which must be one topic from the topic list'
    )
    def jump_to_an_existing_topic(self, topic_name: str):
        if topic_name in self.topic_stack:
            self.topic_stack.remove(topic_name)
        else:
            raise ValueError(f"Unknown existing topic: `{topic_name}`")
        self.topic_stack.append(topic_name)
        return topic_name

    @tool(
        name='Load Topics From a Predefined Task',
        description='useful when you think the user starts a predefined task (a complex topics group).'
                    'All predefined task includs: (separated by comma): ' + ', '.join(predefined_tasks.keys()) +
                    'A predefined task contains a group dialogue topics we define for you, you should distinguish it from topics which are already in topic list'
                    'The input to this tool should be a string representing the name of a predefined task, which must be from (separated by comma): ' + ', '.join(predefined_tasks.keys()) +
                    'You can just use this tool once.'
    )
    def load_topics_from_a_predefined_task(self, task_name: str):
        self.current_task = self.predefined_tasks[task_name]
        main_topic_name = self.topic_type['goal'] + self.current_task['goal']
        self.topic_stack.append(main_topic_name)
        for topic_name in self.current_task['checklist'][::-1]:
            topic_name = self.topic_type['ask'] + topic_name
            self.topic_stack.append(topic_name)
        return main_topic_name + ', ' + ', '.join(topic_name)

    @property
    def tool_description(self) -> str:
        return "\n".join([f'{tool.name}: {tool.description}' for tool in self.tool_list])

    @property
    def tool_names(self) -> str:
        return ", ".join([tool.name for tool in self.tool_list])

    @property
    def tool_by_names(self) -> Dict:
        return {tool.name: tool for tool in self.tool_list}
    
    @property
    def topic_list(self) -> str:
        return '; '.join([topic for topic in self.topic_stack])
    
    def enrich_topic(self, original_topic):
        new_topic = self.topic_enricher.predict(original_topic=original_topic)
        return new_topic
    
    def chat(self, query: str, user_embedder: Embedder=None) -> Tuple[str, List[Document]]:
        """Asks a question and gets the answer.

        Args:
            query: The question to ask.
            user_embedder: An instance of Embedder. Should be the background information specific to the user.

        Returns:
            A tuple containing the answer and a list of related documents.
        """
        current_topic = self.enrich_topic(self.topic_stack[-1])
        # print('<Current topic>: ' + current_topic)

        try:
            if self.background_embedder:
                background_documents = self.background_embedder.search(query, top_k=4)
            else:
                background_documents = []
        except NotFoundError as e:
            background_documents = []
        background_context = '\n===\n'.join(i.page_content for i in background_documents)

        try:
            if user_embedder:
                user_documents = user_embedder.search(query, top_k=4)
            else:
                user_documents = []
        except NotFoundError as e:
            user_documents = []
        user_context = '\n===\n'.join(i.page_content for i in user_documents)    

        result = self.chat_model.predict(human_input=query,
                                         current_topic=current_topic,
                                         task_overview=self.current_task['overview'],
                                         final_goal=self.current_task['goal'],
                                         background_context=background_context,
                                         user_context=user_context)
        return result, background_context, user_context


    def init_topics(self):
        # topics = load_saft_topics()
        # self.topic_stack.extend(topics)
        self.topic_stack.append(self.beginning_topic)
        self.current_task = {
            'overview': None,
            'goal': None,
            'checklist': []
        }

    def parse_agent_output(self, agent_output: str):
        # print('######\n<Agent output>:')
        # print('Thought: ' + agent_output)
        # print('######')
        regex = r"Action: [\[]?(.*?)[\]]?[\n]*Action Input:[\s]*(.*)[\n]*Observation: "
        match = re.search(regex, agent_output, re.DOTALL)
        if not match:
            raise ValueError(f"Output of LLM is not parsable for next tool use: `{agent_output}`")
        tool = match.group(1).strip()
        tool_input = match.group(2)
        tool_input = tool_input.replace('"', '').replace("'", '').strip()
        return tool, tool_input
    
    def do_agent_action(self, tool, tool_input):
        if tool not in self.tool_by_names:
            raise ValueError(f"Unknown tool: {tool}")
        # print('<Tool usage>: ' + tool + ' args: ' + tool_input)
        if tool_input == 'None' or tool_input == None:
            tool_result = self.tool_by_names[tool]()
        else:
            tool_result = self.tool_by_names[tool](tool_input)
        return tool_result

    def run_agent(self, query: str):
        agent_output = self.topic_manage_agent.predict(topic_list=self.topic_list, current_topic=self.topic_stack[-1], tool_description=self.tool_description, tool_names=self.tool_names, human_input=query)
        tool, tool_input = self.parse_agent_output(agent_output)
        tool_result = self.do_agent_action(tool, tool_input)
        return tool_result

    def remove_redundant_topics(self, round_threshold: int=3):
        new_topic_stack = []
        for i, topic_name in enumerate(self.topic_stack):
            if topic_name.startswith(self.topic_type['answer']) and len(self.topic_stack) - i > round_threshold:
                continue
            new_topic_stack.append(topic_name)
        self.topic_stack = new_topic_stack
        

    def run(self, query: str, user_embedder: Embedder=None):
        # print('##########')
        # print('<Stack status 1>: ' + self.topic_list)
        # print('##########')
        self.run_agent(query)
        # print('##########')
        # print('<Stack status 2>:' + '; '.join(self.topic_stack))
        # print('##########')
        self.chat(query, user_embedder)
        self.remove_redundant_topics(3)
    
