import os
import sys
import json

current_directory = os.path.dirname(os.path.abspath(__file__))


def load_a_predefined_task(task_file_path: str):
    task = {
        'task_name': '',
        'overview': '',
        'goal': '',
        'checklist': '',
    }
    with open(task_file_path, 'r') as f:
        obj = json.load(f)
        task['task_name'] = obj['task_name']
        task['overview'] = obj['overview']
        task['goal'] = obj['goal']
        task['checklist'] = obj['checklist']
    return task


def load_a_predefined_task_by_file_name(task_file_name: str):
    if task_file_name == 'medical/basic_diagnosis':
        task_file_path = os.path.join(current_directory, task_file_name + '.json')
        print(task_file_path)
        return load_a_predefined_task(task_file_path)
    else:
        raise ValueError(f"Unknown task file path: {task_file_name}")
        # return None


def load_predefined_tasks():
    task_list = [load_a_predefined_task_by_file_name('medical/basic_diagnosis')]
    tasks = {}
    for task in task_list:
        tasks[task['task_name']] = {
            'overview': task['overview'],
            'goal': task['goal'],
            'checklist': task['checklist'],
        }
    return tasks



if __name__ == '__main__':
    # print(load_saft_topics())
    # load_a_predefined_task('diaggpt/tasks/medical/basic_diagnosis.json')
    print(load_a_predefined_task_by_file_name('medical/basic_diagnosis'))