from random import uniform, randint
from math import floor, ceil
import json

import numpy as np
from scipy.spatial import distance
import mysql.connector
from UserModel import UserModel

from flask import Flask, redirect, url_for, jsonify, escape, request
from flask import send_file, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

db = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="",
  database="kdbas"
)

@app.route('/addData', methods=['POST', 'GET'])
def addData():
    global db
    
    jsonObj = request.get_json()
    email = jsonObj["email"]
    keystroke_string = jsonObj["keystroke"]
    user = UserModel(db, email)

    validation_acc = user.validate_keystroke(keystroke_string)
    if validation_acc < 0.5:
        return json.dumps({'msg':'Inconsistent'})

    user.add(keystroke_string)
    return json.dumps({'msg':'Added'})

@app.route('/predict', methods=['POST', 'GET'])
def predict():
    global db
    
    jsonObj = request.get_json()
    email = jsonObj["email"]
    keystroke_string = jsonObj["keystroke"]
    
    user = UserModel(db, email)
    
    validation_acc = user.validate_keystroke(keystroke_string)
    if validation_acc > 0.5:
        if validation_acc > 0.8:
            user.add(keystroke_string)
        return json.dumps({'msg':'Verified', 'acc': validation_acc})
    else:
        return json.dumps({'msg':'Not Verified', 'acc': validation_acc})

    

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

@app.route('/')
def serve_home():
    return send_file('../frontend/index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
