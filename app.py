from flask import Flask, render_template, request
from flask_cors import CORS
import pymongo
import os

app = Flask(__name__)
CORS(app)
mongo_uri = os.environ.get('MONGODB_URI')
db = pymongo.MongoClient(mongo_uri).get_default_database()
q = db["queue"]

@app.route('/', methods=['GET','POST'])
def main():
## This is manual add mostly for testing purposes
## will remove.
    val = None
    if request.method == 'POST':
        code = request.form['code']
        email = request.form['email']
        doc = q.find_one({"code": code})
        if doc is None:
            doc = {"code": code, "addrs": [email]}
            q.insert_one(doc)
        elif email not in doc["addrs"]:
            doc["addrs"].append(email)
            q.find_one_and_update({'_id': doc['_id']}, {"$set": doc})
        val = 'GOT IT!'
    return render_template('main.html', val=val)

@app.route("/<code>/<name>/<email>")
def re_add(code, name, email):
    doc = q.find_one({"code": code})
    if doc is None:
        doc = {"code": code, "name":name, "addrs": [email]}
        q.insert_one(doc)
    elif email not in doc["addrs"]:
        doc["addrs"].append(email)
        q.find_one_and_update({'_id': doc['_id']}, {"$set": doc})
    return '<html><body><h1>{} has been added to the watchlist for {}!</h1></body></html>'.format(email,code)
