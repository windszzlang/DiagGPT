TOD_CRITERIA = """Criteria of response_quality:
1. Understanding: How well does the system grasp user requests?
2. Relevance: Are the responses directly applicable to the user's needs?
3. Complex Handling: Can the system effectively manage multifaceted queries?
4. Efficiency: How quickly does the system lead the conversation to a resolution?
5. Experience: What is the overall ease and satisfaction of the interaction?
6. Comprehensiveness: Does the system's response provide all the relevant information to fully cover the user's question?
7. Detail: Does the response include sufficient detail and depth to fully address the intricacies and subtleties of the user's inquiry?
8. Sufficiency: Are all aspects and potential implications of the inquiry explored and explained, ensuring that the user receives a thorough understanding of the subject matter?
"""

GRADING_PROMPT_TEMPLATE = """You need to act as an impartial judge and evaluate the quality of a dialogue between a user and a system. Be as objective as possible.
I will provide you the chat history, the evaluation metric, and the evaluation reference.

This dialogue is task-oriented dialogue. In this dialogue, the user and the system needs to achieve a goal and complete a task.
The dialogue needs to go through the entire checklist and then achieve the final goal.
#### task information ####
Topic of dialogue: {topic}
Task which should be completed in this dialogue: {task_name}
Overview of this task: {overview}
Final goal of the task or the dialogue: {goal}
All items in the task checklist: {checklist} (divided by comma)


#### Chat History Start ####
{chat_history}
#### Chat History End ####


You need to evaluate this task-oriented dialogue from three perspectives:
1. completion_quantity: the number of checklist items completed by the system or occured in this chat history.
2. success_rate: a value of 1 or 0, indicating whether this dialogue has achieved the final goal in this dialogue.
3. response_quality: quality of system responses in this task-orinted dialogue. This is rated on a scale of 1 to 10.

""" + TOD_CRITERIA + """

You must provide the evaluation strictly in the JSON format like this:
{{
    "completion_quantity": number,
    "success_rate": number,
    "response_quality": number
}}

Your response of evaluation in JSON: """


#    "explanation": explanation of the value of responsequality


COMPARISON_PROMPT_TEMPLATE = """You need to act as an impartial judge and evaluate the quality of two dialogue between a user and a system. Be as objective as possible.
I will provide you two chat history, the evaluation metric, and the evaluation reference.

This dialogue is task-oriented dialogue. In this dialogue, the user and the system needs to achieve a goal and complete a task.
The dialogue needs to go through the entire checklist and then achieve the final goal.
#### task information ####
Topic of dialogue: {topic}
Task which should be completed in this dialogue: {task_name}
Overview of this task: {overview}
Final goal of the task or the dialogue: {goal}
All items in the task checklist: {checklist} (divided by comma)


#### Dialogue A Start ####
{chat_history_a}
#### Dialogue A End ####

#### Dialogue B Start ####
{chat_history_b}
#### Dialogue B End ####

You need to evaluate two task-oriented dialogue based on the quality of system responses in this task-orinted dialogue.
This is rated on a scale of 0 to 10.

""" + TOD_CRITERIA + """

You must provide the evaluation strictly in the JSON format like this:
{{
    "score_a": number from 0 to 10 (score of dialogue A),
    "score_b": number from 0 to 10 (score of dialogue B),
    "winner": "A" or "B" but cannot tie,
    "explanation": "explanation of your evaluation in one line"
}}

Your response of evaluation in JSON:"""


