import os
import json
from tqdm import tqdm

from usergpt.main import UserGPT
from chatgpt.main import ChatGPT
from diaggpt.main import DiagGPT
from evalgpt.main import EvalGPT


# system_moodel = 'chatgpt'
system_moodel = 'chatgpt-3.5'
# system_moodel = 'diaggpt'
print(system_moodel)

show_chat = True
# show_chat = False

round_threshold = 10 # data


with open('openai_api_key.txt') as f:
    os.environ['OPENAI_API_KEY'] = f.read()

data = []
with open('data/LLM-TOD/data.jsonl') as f:
    for line in f.readlines():
        data.append(json.loads(line))


for D in tqdm(data):
    output_path = 'exp_output/' + system_moodel + '/' + str(D['id']) + '.json'
    if os.path.exists(output_path):
        continue

    user = UserGPT(D['topic'], D['task_name'], D['user_role'])
    if system_moodel == 'chatgpt':
        system = ChatGPT(D['topic'], D['task_name'], D['overview'], D['goal'], D['checklist'], 'gpt-4-0613')
    elif system_moodel == 'chatgpt-3.5':
        system = ChatGPT(D['topic'], D['task_name'], D['overview'], D['goal'], D['checklist'], 'gpt-3.5-turbo-0613')
    elif system_moodel == 'diaggpt':
        system = DiagGPT('gpt-4-0613')

    user_msg = user.user_greeting
    system_msg = system.chat(user_msg)
    if show_chat:
        print('User:', user_msg, '\n')
        print('System:', system_msg, '\n')

    new_D = {'chat_history': [
        {'user': user_msg, 'system': system_msg}
    ]}

    cnt = 0
    while True:
        cnt += 1
        user_msg = user.chat(system_msg)
        system_msg = system.chat(user_msg)
        if show_chat:
            print('User:', user_msg, '\n')
            print('System:', system_msg, '\n')
        new_D['chat_history'].append({
            'user': user_msg, 'system': system_msg
        })
        if 'bye' in system_msg:
            break
        if cnt >= round_threshold:
            new_D['chat_history'].append({'user': '', 'system': ''})
            break
    with open(output_path, 'w') as f:
        json.dump(new_D, f)
    # break



## Evaluate
mode = 'grading'
# mode = 'comparsion'

if mode == 'grading':
    eval_results = []
    eval_model = EvalGPT('gpt-4-turbo-2024-04-09')
    directory_path = 'exp_output/' + system_moodel + '/'
    for i, task_info in enumerate(tqdm(data)):
        file_path = os.path.join(directory_path, str(i) + '.json')
        with open(file_path) as f:
            D = json.load(f)
        chat_history = D['chat_history']

        eval_result = eval_model.eval(task_info, chat_history)
        print(eval_result)
        eval_results.append(eval_result)


    num = len(eval_results)
    efficiency = sum([e['efficiency'] for e in eval_results]) / num
    completion_rate = sum([e['completion_rate'] for e in eval_results]) / num
    success_rate = sum([e['success_rate'] for e in eval_results]) / num
    response_quality = sum([e['response_quality'] for e in eval_results]) / num


    final_results = {
        "efficiency": efficiency,
        "completion_rate": completion_rate,
        "success_rate": success_rate,
        "response_quality": response_quality
    }
    print(final_results)
    with open('exp_output/' + system_moodel + '.json', 'w') as f:
        json.dump(final_results, f)

elif mode == 'comparsion':
    # system_a = 'chatgpt'
    # system_b = 'diaggpt'

    system_a = 'diaggpt'
    system_b = 'chatgpt'

    eval_results = {
        'A': 0,
        'B': 0
    }
    eval_model = EvalGPT('gpt-4-turbo-2024-04-09')
    directory_path_a = 'exp_output/' + system_a + '/'
    directory_path_b = 'exp_output/' + system_b + '/'
    for i, task_info in enumerate(tqdm(data)):
        file_path_a = os.path.join(directory_path_a, str(i) + '.json')
        file_path_b = os.path.join(directory_path_b, str(i) + '.json')
        with open(file_path_a) as f:
            chat_history_a = json.load(f)['chat_history']
        with open(file_path_b) as f:
            chat_history_b = json.load(f)['chat_history']

        eval_result = eval_model.compare(task_info, chat_history_a, chat_history_b)
        print(eval_result)
        eval_results[eval_result['winner']] += 1
        # input()

    print(eval_results)
    with open('exp_output/comp_' + system_a + '_a.json', 'w') as f:
        json.dump(eval_results, f)