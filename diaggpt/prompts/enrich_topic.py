ENRICH_TOPIC_PROMPT = """Your objective is to enrich dialogue topics between a professional staff and a user. I will give you an original and simple topic, and you need to give me an enriched topic based on the original one and my needs.
The new enriched topic will be used by a professional staff, which is also trained from ChatGPT, like you. This topic can be thought of as a prompt. The professional staff need to first understand the new topic and then talk to users about this topic.
If you give a better topic to the professional staff, it can have a better dialogue with users, so craft the best possible topic (prompt) for my needs.

Make sure that the professional staff can understand it easily!
Your new topic needs to for professional staffs to tell it what to do, not users!
Your new topic needs to for professional staffs to tell it what to do, not users!
Your new topic needs to for professional staffs to tell it what to do, not users!

You need to consider previous chat history with the user to detail and improve the original topic:
###### Chat History START ###### (NOTE: do not use chat history in your topic directly)
{chat_history}
###### Chat History END ######


Provide your new topic. Your new topic is limited to 30 words. Remember your new topic needs to for professional staffs to tell it what to do, not users!

Begin!

Original Topic: {original_topic}
New Topic:
"""