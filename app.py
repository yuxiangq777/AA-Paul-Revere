from flask import Flask, render_template, request
from flask_cors import CORS
import pymongo
import os

app = Flask(__name__)
CORS(app)
db = pymongo.MongoClient(os.environ.get('MONGODB_URI')).get_default_database()

@app.route("/<code>/<name>/<email>")
def add(code, name, email):
    doc = db["queue"].find_one({"code": code})
    if doc is None:
        db["queue"].insert_one({"code": code, "name":name, "addrs": [email]})
    elif email not in doc["addrs"]:
        doc["addrs"].append(email)
        db["queue"].find_one_and_update({'_id': doc['_id']}, {"$set": doc})
    return '<html><body><h1>{} has been added to the watchlist for {}!</h1></body></html>'.format(email,code)
