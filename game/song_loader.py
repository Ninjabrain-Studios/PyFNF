import json

def load_song_notes(path):
    with open(path, "r") as f:
        return json.load(f)
