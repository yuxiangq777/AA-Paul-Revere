from flask import Flask, render_template, request
from flask_cors import CORS
import urllib
import pymongo
import config
import random

app = Flask(__name__)
CORS(app)
db = pymongo.MongoClient(config.MONGODB_URI).get_default_database()

CREDITS = [
    '''
    Photo Credit: Emre Erdogmus<br>
    Shot on iPhone XR<br>
    IG Photography account: <a href="https://www.instagram.com/emresfotos/" target="_blank">@emresfotos</a>
    ''',
    '''
    Photo Credit: Lavanya Kukkemane<br>
    Instagram: @lavanyak814
    ''',
    '''
    Photo Credit: Calvin Harris Belcher
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    ''',
    '''
    Photo Credit: Benedict Chua
    '''
]

@app.route("/email/<code>/<name>/<email>")
def add_email(code, name, email):
    lucky = random.randrange(0, len(CREDITS))
    name = urllib.parse.unquote(name)

    doc = db["queue"].find_one({"code": code})
    if doc is None: #course not in db yet
        db["queue"].insert_one({"code": code, "name":name, "emails": [email], "nums": []})
    elif email not in doc["emails"]: #email not added already
        doc["emails"].append(email)
        db["queue"].find_one_and_update({'_id': doc['_id']}, {"$set": doc})
    else: #already in the db
        msg = '{} was already on the email watchlist for {} {}!'.format(email,code,name)
        return render_template("landing.html", img_link = "https://www.ics.uci.edu/~rang1/PRL/bg_img/bg{}.jpg".format(lucky), message=msg, credits=CREDITS[lucky])

    msg = '{} has been added to the email watchlist for {} {}!</h1></body></html>'.format(email,code,name)
    return render_template("landing.html", img_link = "https://www.ics.uci.edu/~rang1/PRL/bg_img/bg{}.jpg".format(lucky), message=msg, credits=CREDITS[lucky])

@app.route("/sms/<code>/<name>/<num>")
def add_sms(code, name, num):
    lucky = random.randrange(len(CREDITS))
    name = urllib.parse.unquote(name)

    doc = db["queue"].find_one({"code": code})
    if doc is None: #course not in db yet
        db["queue"].insert_one({"code": code, "name":name, "emails": [], "nums": [num]})
    elif num not in doc["nums"]: #number not added already
        doc["nums"].append(num)
        db["queue"].find_one_and_update({'_id': doc['_id']}, {"$set": doc})
    else: #already in the db
        msg = '{} was already on the sms watchlist for {} {}!'.format(num,code,name)
        return render_template("landing.html", img_link = "https://www.ics.uci.edu/~rang1/PRL/bg_img/bg{}.jpg".format(lucky), message=msg, credits=CREDITS[lucky])
    msg = '<html><body><h1 id=\"findme\">{} has been added to the sms watchlist for {} {}!</h1></body></html>'.format(num,code,name)
    return render_template("landing.html", img_link = "https://www.ics.uci.edu/~rang1/PRL/bg_img/bg{}.jpg".format(lucky), message=msg, credits=CREDITS[lucky])

if __name__ == '__main__':
    app.debug = True
    app.run()
