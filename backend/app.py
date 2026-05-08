from flask import Flask, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

@app.route("/places")
def places():

    with open(
        "data/cleaned_places.json",
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    return jsonify(data)

app.run(debug=True)