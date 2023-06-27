MANAGE_TOPIC_PROMPT = """Your objective is to manage dialogue topic in the dialogue between a AI ____ expert and a user.
The diaglogue topics are always about the ____ field. If you can effectively manage topics, the AI ____ expert can have a better dialogue with users
You now have a topic list which contains all existing topics in the entire dialogues in order, which are separated by semicolon (; ): {topic_list}.

The current dialogue topic is the last topic in the topic list, which is {current_topic}.

You need to manage dialogue topics as best as you can using the following tools: 

{tool_description}

###### Chat History START ###### (you can consider previous chat history between the AI ____ expert and the user)
{chat_history}
###### Chat History END ######

You must use the following format, including User Input, Thought, Action, Action Input, and Observation:

User Input: the input from the user
Thought: comment on what you want to do next
Action: the action to take, exactly one element of [{tool_names}]
Action Input: the input to the action (if you are using a tool without input, Action Input should be None)
Observation: the result of the action (STOP here)

###### STOP ###### (just think one round, after give Observation, you must STOP! STOP! STOP!)

Begin!

User Input: {human_input}
Thought: (HINT: focus on the last output of AI medical expert the current input of the user)
"""