import flask
from threading import Thread
app = flask.Flask(__name__)
@app.route("/")
def index():
  return "Bot Working"

def runapp():
  app.run("0.0.0.0", port = 6969)
def run():
  Thread(target = runapp).start()