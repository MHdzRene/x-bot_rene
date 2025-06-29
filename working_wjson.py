import json


def save_to_json(dictionary,filename):
    with open(filename,'w') as file:
        json.dump(dictionary,file)

def load_from_json(filename):
    with open(filename, 'r') as file:
        dictionary=json.load(file)
    return dictionary




