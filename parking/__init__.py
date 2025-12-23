from flask import Flask

app = Flask(__name__)

@app.route("/")
def coming_soon():
  return "👋 Coming Soon...!"
