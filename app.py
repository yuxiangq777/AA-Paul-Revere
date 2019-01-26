from flask import Flask, render_template, request
from flask_cors import CORS
from fbchat import Client
from fbchat.models import *
import pymongo
import os
import redis
import json

app = Flask(__name__)
CORS(app)
db = pymongo.MongoClient(os.environ.get('MONGODB_URI')).get_default_database()
r = redis.from_url(os.environ.get('REDISCLOUD_URL'))

@app.route("/email/<code>/<name>/<email>")
def add_email(code, name, email):
    if r.get(email) == None: #first time
        r.set(email,'e')
    doc = db["queue"].find_one({"code": code})
    if doc is None: #course not in db yet
        db["queue"].insert_one({"code": code, "name":name, "emails": [email], "fbs": []})
    elif email not in doc["emails"]: #email not added already
        doc["emails"].append(email)
        db["queue"].find_one_and_update({'_id': doc['_id']}, {"$set": doc})
    else: #already in the db
        return '<html><body><h1 id=\"findme\">{} is already on the email watchlist for {} {}!</h1></body></html>'.format(email,code,name)
    return '<html><body><h1 id=\"findme\">{} has been added to the email watchlist for {} {}!</h1></body></html>'.format(email,code,name)

@app.route("/facebook/<code>/<name>/<fb>")
def add_fb(code, name, fb):
    if r.get(fb) == None: #first time
        r.set(fb,'f')
        client = Client(os.environ.get('USERNAME'), os.environ.get('PASSWORD'))
        try:
            client.send(Message(text='Hi! AntAlmanac here. This is to confirm that you just signed up for FB Messenger notifications. Please respond \"zot\" to this message or move this conversation so that you can get notified the next time we message. If you did not initiate this request, please ignore this message. Thank you!'),
                    thread_id=fb, thread_type=ThreadType.USER)
        except:
            #return '<html><body><h1 id=\"findme\">{} is an invalid Facebook id!</h1></body></html>'.format(fb)
            return json.dumps({"message":"{} is an invalid Facebook id!".format(fb)})
        client.logout()
    doc = db["queue"].find_one({"code": code})
    if doc is None: #course not in db yet
        db["queue"].insert_one({"code": code, "name":name, "emails":[], "fbs": [fb]})
    elif fb not in doc["fbs"]: #if fb not added already
        doc["fbs"].append(fb)
        db["queue"].find_one_and_update({'_id': doc['_id']}, {"$set": doc})
    else: #already in the db
        #return '<html><body><h1 id=\"findme\">{} is already on the FB watchlist for {} {}!</h1></body></html>'.format(fb,code,name)
        return json.dumps({"message":"{} is already on the FB watchlist for {} {}".format(fb,code,name)})
    #return '<html><body><h1 id=\"findme\">{} has been added to the FB watchlist for {} {}!</h1></body></html>'.format(fb,code,name)
    return json.dumps({"message":"{} has been added to the FB watchlist for {} {}".format(fb,code,name)})
