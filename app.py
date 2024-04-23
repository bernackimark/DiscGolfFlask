from flask import Flask, render_template
from pathlib import Path

import events
import players

app = Flask(__name__)
basedir = Path(__file__).parent.resolve()

@app.route('/')
def home():
    return render_template("streamlit.html")
    # return '<h1>Whats up slappers?</h1>'

@app.route('/api/players')
def all_players() -> list[dict]:
    return players.get_all_players()

@app.route('/api/results')
def all_results() -> list[dict]:
    return events.get_all_event_results()


if __name__ == "__main__":
    app.run(debug=True)
