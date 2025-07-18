import json


def save_to_json(dictionary,filename):
    # Prevent saving None or empty dicts (unless explicitly intended)
    if dictionary is None:
        return
    if isinstance(dictionary, dict) and len(dictionary) == 0:
        return
    with open(filename,'w') as file:
        json.dump(dictionary,file)

def load_from_json(filename):
    with open(filename, 'r') as file:
        dictionary=json.load(file)
    return dictionary




