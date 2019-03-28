from leadsheet.backend.render import Song

import json


with open('../examples/example_song.json', 'r') as song:
    jdoc = json.loads(song.read())
    page = Song(jdoc)
    page.render_pdf()
