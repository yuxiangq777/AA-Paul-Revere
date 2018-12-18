import pymongo
import os
import urllib.parse
import requests
import bs4 as bs
import sendgrid
from sendgrid.helpers.mail import *

TERM = '2019-03'
WEBSOC = 'https://www.reg.uci.edu/perl/WebSoc?'
BATCH_SIZE = 8

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
from_email = Email("AntAlmanac@gmail.com")
qa_email = Email(os.environ.get('QA_EMAIL'))

db = pymongo.MongoClient(os.environ.get('MONGODB_URI')).get_default_database()
q, names = {}, {}
for course in db.queue.find():
    q[course['code']] = course['addrs']
    names[course['code']] = course['name']

def fetch_statuses(targets):
    statuses = {code:None for code in targets} #is statuses even a word in english? | initialize status values

    iter = targets.__iter__()
    for i in range(len(targets)//BATCH_SIZE + 1):
        codes = set()
        for _ in range(BATCH_SIZE):
            try:
                codes.add(next(iter))
            except: #Expecting a StopIteration
                break

        # get status values for these codes
        fields = [('YearTerm',TERM),('CourseCodes',', '.join(codes)),('ShowFinals',0),('ShowComments',0),('CancelledCourses','Include')]
        url = WEBSOC + urllib.parse.urlencode(fields)
        print(url)

        sauce = requests.get(url, headers=HEADERS).content
        print(sauce)
        sp = bs.BeautifulSoup(sauce, 'lxml')

        for row in sp.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) > 15 and cells[0].text in statuses:
                code = cells[0].text
                statuses[code] = cells[-1].text

    return statuses

statuses = fetch_statuses(q.keys())
print(statuses)
double_check = fetch_statuses([code for code, status in statuses.items() if status != 'FULL'])
print(double_check)
for code, status in double_check.items():
    if status != statuses[code]: ## If the two samples disagree, then we say it's FULL
        statuses[code] = 'FULL'
print(double_check)

for code, status in statuses.items():
    course_url = WEBSOC + urllib.parse.urlencode([('YearTerm',TERM),('CourseCodes',code),('ShowFinals',0),('ShowComments',0),('CancelledCourses','Include')])
    if status is None or status == 'FULL' or status == 'NewOnly':
        continue #keep waiting
    else:
        if status == 'Waitl':
            msg = '<html><p>Space just opened up <strong>on the waitlist</strong> for {} with code, {} ({}).</p>'.format(names[code], code, course_url)
        if status == 'OPEN':
            msg = '<html><p>Space just opened up in {} with code, {} ({}).</p>'.format(names[code], code, course_url)

    ##send notifications
    for house in q[code]:
        to_email = Email(house)
        subject = "[AntAlmanac Notifications] Space Just Opened Up to Enroll"
        content = Content("text/html", msg+'<p>Here\'s WebReg while we\'re at it: <a href="https://www.reg.uci.edu/registrar/soc/webreg.html" target="_blank">WebReg</a></p><p>You have been removed from this watchlist; to add yourself again, please visit <a href="https://antalmanac.com" target="_blank">AntAlmanac</a> or click on <a href="http://mediaont.herokuapp.com/{}/{}/{}" target="_blank">this link</a></p><p>Also, was this notification correct? Were you able to add yourself? Please do let us know asap if there is anything that isn\'t working as it should be!!! <a href="https://goo.gl/forms/U8CuPs05DlIbrSfz2" target="_blank">Give (anonymous) feedback!</a></p><p>Yours sincerely,</p><p>Poor Peter\'s AntAlmanac</p></html>'.format(code, names[code], house))
        mail = Mail(from_email, subject, to_email, content)
        response = sg.client.mail.send.post(request_body=mail.get())
        mail = Mail(from_email, subject, qa_email, content) #For quality assurance purposes
        response = sg.client.mail.send.post(request_body=mail.get()) #For quality assurance
        print(code, 'Done')

    db.queue.delete_one({"code": str(code)})
