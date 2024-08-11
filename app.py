from flask import Flask, render_template
from pathlib import Path

from controller.event import EventResults
from controller import player

app = Flask(__name__)
basedir = Path(__file__).parent.resolve()

@app.route('/')
def home():
    return '<h1>Whats up slappers?</h1>'

@app.route('/disc_golf')
def disc_golf():
    return render_template("disc_golf.html")

@app.route('/dg2')
def dg_admin():
    return render_template("dg2.html")

@app.route('/api/players')
def all_players() -> list[dict]:
    return players.get_all_players()

@app.route('/api/event_results_flat')
def event_results_flat() -> list[dict]:
    results = EventResults()
    return results.event_results_flat

@app.route('/api/event_results_nested')
def event_results() -> list[dict[str, dict]]:
    results = EventResults()
    return results.event_results_nested


if __name__ == "__main__":
    app.run(debug=True)
