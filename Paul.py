import pymongo
import os
import urllib.request
import urllib.parse
import bs4 as bs
import sendgrid
from sendgrid.helpers.mail import *

TERM = '2019-03'
WEBSOC = 'https://www.reg.uci.edu/perl/WebSoc?'
BATCH_SIZE = 25

sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
from_email = Email("AntAlmanac@gmail.com")

db = pymongo.MongoClient(os.environ.get('MONGODB_URI')).get_default_database()
q, names = {}, {}
for course in db.queue.find():
    q[int(course['code'])] = course['addrs']
    names[int(course['code'])] = course['name']
statuses = {code:None for code in q.keys()} #is statuses even a word in english? | initialize status values

iter = q.keys().__iter__()
for i in range(len(q)//BATCH_SIZE + 1):
    codes = set()
    for _ in range(BATCH_SIZE):
        try:
            codes.add(str(next(iter)))
        except: #Expecting a StopIteration
            break

    # get status values for these codes
    fields = [('YearTerm',TERM),('CourseCodes',', '.join(codes)),('ShowFinals',0),('ShowComments',0),('CancelledCourses','Include')]
    url = WEBSOC + urllib.parse.urlencode(fields)
    sp = bs.BeautifulSoup(urllib.request.urlopen(url), 'lxml')

    for row in sp.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) > 15 and int(cells[0].text) in statuses:
            code = int(cells[0].text)
            statuses[code] = cells[-1].text

for code, status in statuses.items():
    course_url = WEBSOC + urllib.parse.urlencode([('YearTerm',TERM),('CourseCodes',str(code)),('ShowFinals',0),('ShowComments',0),('CancelledCourses','Include')])
    if status is None:
        msg = '<html><p>It seems that {} with code, {} ({}), has been cancelled!</p>'.format(names[code], code, course_url)
    elif status == 'FULL' or status == 'NewOnly':
        continue #keep waiting
    else:
        if status == 'Waitl':
            msg = '<html><p>Space just opened up on the waitlist for {} with code, {} ({}).</p>'.format(names[code], code, course_url)
        if status == 'OPEN':
            msg = '<html><p>Space just opened up in {} with code, {} ({}).</p>'.format(names[code], code, course_url)

    ##send notifications
    for house in q[code]:
        to_email = Email(house)
        subject = "[AntAlmanac Notifications] Space Just Opened Up to Enroll"
        content = Content("text/html", msg+'<p>You have been removed from this watchlist; to add yourself again, please visit <a href="https://antalmanac.com" target="_blank">AntAlmanac</a> or click on <a href="http://mediaont.herokuapp.com/{}/{}" target="_blank">this link</a></p><p>Yours sincerely,</p><p>Poor Peter\'s AntAlmanac</p></html>'.format(code, house))
        mail = Mail(from_email, subject, to_email, content)
        response = sg.client.mail.send.post(request_body=mail.get())
        print(code, 'Done')

    q.delete_one({"code": str(code)})
