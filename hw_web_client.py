from time import time

import requests

task1 = {
    'status': 'active',
    'expires': time() + 20,
    'name': 'meow1',
    'description': 'meow1',
}
task2 = {
    'status': 'active',
    'expires': time() + 25,
    'name': 'meow2',
    'description': 'meow2',
}
task3 = {
    'status': 'active',
    'expires': time() + 30,
    'name': 'meow3',
    'description': 'meow3',
}


if __name__ == '__main__':
    resp = requests.post('http://localhost:5000/api/tasks', json=[task1, task2, task3])

    resp1 = requests.put('http://localhost:5000/api/tasks/meow1', json={'key': 'name', 'value': 'meowx'})

    print(requests.get('http://localhost:5000/api/tasks/meowx').text)

    print(requests.get('http://localhost:5000/api/tasks/all').text)

    print(requests.get('http://localhost:5000/api/tasks/active').text)
    print(requests.get('http://localhost:5000/api/tasks/expired').text)
    print(requests.get('http://localhost:5000/api/tasks/done').text)

    resp2 = requests.put('http://localhost:5000/api/priority/meow3/1')
    print(requests.get('http://localhost:5000/api/tasks/all').text)

    resp3 = requests.delete('http://localhost:5000/api/tasks/meow2')
    print(requests.get('http://localhost:5000/api/tasks/all').text)
