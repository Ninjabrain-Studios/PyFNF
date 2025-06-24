import json

def load_song_notes(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
