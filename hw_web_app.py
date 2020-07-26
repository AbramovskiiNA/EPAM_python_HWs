from time import time
from typing import Dict

from flask import Flask, request


class ToDoList:
    def __init__(self):
        self.tasks = []

    def add_tasks(self, *tasks: Dict):
        now = time()
        _ = [t.update({'added': now}) for t in tasks]

        self.tasks.extend(tasks)

    def edit_task(self, task_name: str, key: str, value):
        to_edit = next(t for t in self.tasks if t['name'] == task_name)
        to_edit[key] = value

    def remove_task(self, task_name: str):
        to_remove = next(t for t in self.tasks if t['name'] == task_name)
        self.tasks.remove(to_remove)

    def modify_task_priority(self, task_name: str, priority_value: str):
        """Moves task up by specified positions number.
        Or, puts it at the top/bottom of list if highest/lowest specified respectively."""

        to_edit = next(t for t in self.tasks if t['name'] == task_name)
        ix = self.tasks.index(to_edit)
        self.tasks.remove(to_edit)

        if priority_value == 'highest':
            new_ix = 0
        elif priority_value == 'lowest':
            new_ix = len(self.tasks)
        else:
            new_ix = ix - int(priority_value)
            if new_ix < 0:
                new_ix = 0

        self.tasks.insert(new_ix, to_edit)

    def pprint_tasks(self, key: str, *values) -> str:
        self._handle_done_and_expired_tasks()

        if key == 'all':
            match = self.tasks
        else:
            match = (t for t in self.tasks if t[key] in values)

        output = f"{'Name':>15}\t{'Description':<25} {'Status'}\n"
        for t in match:
            output += f"{t['name']:>15}\t{t['description']:<25} {t['status']}\n"
        return output

    def _handle_done_and_expired_tasks(self):
        for task in self.tasks:
            expires = task.get('expires')
            if expires:
                if float(expires) < time():
                    task['status'] = 'expired'

        sort_dict = {
            'active': 0,
            'expired': 1,
            'done': 2
        }

        self.tasks.sort(key=lambda t: sort_dict[t['status']])


todolist = ToDoList()
app = Flask(__name__)


@app.route('/api/tasks', methods=['GET'])
def retieve_all_tasks():
    return todolist.pprint_tasks('all')


@app.route('/api/tasks/<task_name>', methods=['GET'])
def retieve_task(task_name: str):
    return todolist.pprint_tasks('name', task_name)


@app.route('/api/<task_status>', methods=['GET'])
def retieve_tasks_of_status(task_status: str):
    return todolist.pprint_tasks('status', task_status)


@app.route('/api/tasks', methods=['POST'])
def add_tasks():
    todolist.add_tasks(*request.json)
    return 'Tasks added', 200


@app.route('/api/tasks/<task_name>', methods=['PUT'])
def edit_task(task_name: str):
    resp = request.json
    todolist.edit_task(task_name, resp['key'], resp['value'])
    return 'Task edited', 200


@app.route('/api/tasks/<task_name>', methods=['DELETE'])
def remove_task(task_name: str):
    todolist.remove_task(task_name)
    return 'Task removed', 200


@app.route('/api/priority/<task_name>/<priority_value>', methods=['PUT'])
def change_priority(task_name: str, priority_value: str):
    todolist.modify_task_priority(task_name, priority_value)
    return 'Task priority changed', 200


@app.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


if __name__ == '__main__':
    app.run()
