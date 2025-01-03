from flask import Flask, redirect, render_template, url_for
from pathlib import Path

from controller.event import EventResults
from controller import player

app = Flask(__name__)
basedir = Path(__file__).parent.resolve()

@app.route('/')
def home():
    return redirect(url_for('disc_golf'))
    # return '<h1>Whats up slappers?</h1>'

@app.route('/?utm_medium=oembed')
def disc_golf():
    return render_template("disc_golf.html")

@app.route('/dg2')
def dg_admin():
    return render_template("dg2.html")

@app.route('/api/players')
def all_players() -> list[dict]:
    return player.get_all_players()

@app.route('/api/results_flat')
def event_results_flat() -> list[dict]:
    results = EventResults()
    return results.results_flat

@app.route('/api/event_results')
def event_results() -> list[dict[str: dict]]:
    results = EventResults()
    return results.results


if __name__ == "__main__":
    app.run(debug=True)
