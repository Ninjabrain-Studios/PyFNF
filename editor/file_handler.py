import json

def save_map(path, map_data):
    with open(path, "w") as f:
        json.dump(map_data, f, indent=2)

def load_map(path):
    with open(path, "r") as f:
        return json.load(f)
