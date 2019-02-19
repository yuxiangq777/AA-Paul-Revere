from flask import Flask, render_template, request
from flask_cors import CORS
import pymongo
import config

app = Flask(__name__)
CORS(app)
db = pymongo.MongoClient(config.MONGODB_URI).get_default_database()
r = redis.from_url(config.REDISCLOUD_URL)

@app.route("/email/<code>/<name>/<email>")
def add_email(code, name, email):
    if r.get(email) == None: #first time
        r.set(email,'e')
    doc = db["queue"].find_one({"code": code})
    if doc is None: #course not in db yet
        db["queue"].insert_one({"code": code, "name":name, "emails": [email], "nums": []})
    elif email not in doc["emails"]: #email not added already
        doc["emails"].append(email)
        db["queue"].find_one_and_update({'_id': doc['_id']}, {"$set": doc})
    else: #already in the db
        return '<html><body><h1 id=\"findme\">{} is already on the email watchlist for {} {}!</h1></body></html>'.format(email,code,name)
    return '<html><body><h1 id=\"findme\">{} has been added to the email watchlist for {} {}!</h1></body></html>'.format(email,code,name)

@app.route("/sms/<code>/<name>/<num>")
def add_sms(code, name, num):
    if r.get(num) == None: #first time
        r.set(num,'s')
    doc = db["queue"].find_one({"code": code})
    if doc is None: #course not in db yet
        db["queue"].insert_one({"code": code, "name":name, "emails": [], "nums": [num]})
    elif num not in doc["nums"]: #number not added already
        doc["nums"].append(num)
        db["queue"].find_one_and_update({'_id': doc['_id']}, {"$set": doc})
    else: #already in the db
        return '<html><body><h1 id=\"findme\">{} is already on the sms watchlist for {} {}!</h1></body></html>'.format(num,code,name)
    return '<html><body><h1 id=\"findme\">{} has been added to the sms watchlist for {} {}!</h1></body></html>'.format(num,code,name)
