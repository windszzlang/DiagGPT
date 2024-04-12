import json
import re
import openai

from langchain import LLMChain, PromptTemplate
from langchain.chat_models import ChatOpenAI

from .prompt import GRADING_PROMPT_TEMPLATE, COMPARISON_PROMPT_TEMPLATE



class EvalGPT:

    def __init__(self, model_name='gpt-4-turbo'):
        self.model_name = model_name
        self.grading_eval_model, self.comparison_eval_model = self._init_eval_model()

    def _init_eval_model(self):
        grading_prompt = PromptTemplate(input_variables=['topic', 'task_name', 'overview', 'goal', 'checklist', 'chat_history'], template=GRADING_PROMPT_TEMPLATE)
        grading_chain = LLMChain(llm=ChatOpenAI(model_name=self.model_name, temperature=0), prompt=grading_prompt)
        
        comparison_prompt = PromptTemplate(input_variables=['topic', 'task_name', 'overview', 'goal', 'checklist', 'chat_history_a', 'chat_history_b'], template=COMPARISON_PROMPT_TEMPLATE)
        comparison_chain = LLMChain(llm=ChatOpenAI(model_name=self.model_name, temperature=0), prompt=comparison_prompt)
        
        return grading_chain, comparison_chain
  
    def extract_json_from_output(self, text):
        pattern = r"```json\n([\s\S]+?)\n```"
        matched_json = re.search(pattern, text)
        if matched_json:
            extracted_json = matched_json.group(1)
            return extracted_json
        else:
            # backup plan
            pattern = r"\{.*?\}"
            matched_json = re.search(pattern, text, re.DOTALL)
            if matched_json:
                extracted_json = matched_json.group()
                return extracted_json
            else:
                raise ValueError('No JSON structure found.')
    

    def eval(self, task_info, chat_history):
        results = self.grading_eval_model.predict(
            topic=task_info['topic'],
            task_name=task_info['task_name'], 
            overview=task_info['overview'], 
            goal=task_info['goal'],
            checklist=json.dumps(task_info['checklist']),
            chat_history=json.dumps(chat_history))
        results = json.loads(self.extract_json_from_output(results))
        
        results['efficiency'] = len(chat_history)
        results['completion_rate'] = results['completion_quantity'] / len(task_info['checklist'])

        return results
    
    def compare(self, task_info, chat_history_a, chat_history_b):
        results = self.comparison_eval_model.predict(
            topic=task_info['topic'],
            task_name=task_info['task_name'], 
            overview=task_info['overview'], 
            goal=task_info['goal'],
            checklist=json.dumps(task_info['checklist']),
            chat_history_a=json.dumps(chat_history_a),
            chat_history_b=json.dumps(chat_history_b))

        results = json.loads(self.extract_json_from_output(results))

        return results