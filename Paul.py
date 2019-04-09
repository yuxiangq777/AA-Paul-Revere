import pymongo
import urllib.parse
import requests
import bs4 as bs
import sendgrid
import config
import urllib
from sendgrid.helpers.mail import *
import boto3

TERM = '2019-14'
WEBSOC = 'https://www.reg.uci.edu/perl/WebSoc?'
TINYURL="http://tinyurl.com/api-create.php"
BATCH_SIZE = 8

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
aws = boto3.client(
    "sns",
    aws_access_key_id=config.AWS_ACCESSKEYID,
    aws_secret_access_key=config.AWS_SECRECTKEY,
    region_name="us-east-1"
)

TINY_URL = "http://tinyurl.com/api-create.php"

def shorten(long_url):
    try:
        url = TINY_URL + "?" \
            + urllib.parse.urlencode({"url": long_url})
        res = requests.get(url)
        # print("LONG URL:", long_url) # original url
        # print("SHORT URL:", res.text) # shortened version
        return res.text if len(res.text)<50 else long_url # return shorten url
    except Exception as e:
        return long_url # if unable to get shorten url, just return back the long one

# initialize senders
while 1:
    print("run")
    sg = sendgrid.SendGridAPIClient(config.SENDGRID_API_KEY)
    from_email = Email("AntAlmanac@gmail.com")
    qa_email = Email(config.QA_EMAIL)

    db = pymongo.MongoClient(config.MONGODB_URI).get_database()

    # initialize variables...
    emails, nums, names = {}, {}, {}
    for course in db.queue.find():
        code = course['code']
        emails[code] = course['emails']
        nums[code] = course['nums']
        names[code] = course['name']

    ##helpers
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
            # print(url)

            sp = bs.BeautifulSoup(requests.get(url, headers=HEADERS).content, 'lxml')

            for row in sp.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) > 14 and cells[0].text in statuses:
                    code = cells[0].text
                    statuses[code] = cells[-1].text

        return statuses

    statuses = fetch_statuses(emails.keys())
   # print(statuses)

    for code, status in statuses.items():
        if status is None:
            course_url = WEBSOC + urllib.parse.urlencode([('YearTerm',TERM),('CourseCodes',code),('CancelledCourses','Include')])
            msg = '{}. Code: {} ({}) has been cancelled'.format(names[code], code, shorten(course_url)) # shorten the course_url
        elif status == 'FULL' or status == 'NewOnly':
            continue #keep waiting
        else:
            course_url = shorten(WEBSOC + urllib.parse.urlencode([('YearTerm',TERM),('CourseCodes',code)])) # shorten the course_url
            if status == 'Waitl':
                msg = 'Waitlist opened for {}. Code: {} ({}). '.format(names[code], code, course_url)
            if status == 'OPEN':
                msg = 'Space opened in {}. Code: {} ({}). '.format(names[code], code, course_url)

        #send email notifications
        print('emails')
        for house in emails[code]:
            to_email = Email(house)
            subject = "[AntAlmanac Notifications] Space Just Opened Up"
            content = Content("text/html",'<html><p>'+msg+'</p><p>Here\'s WebReg while we\'re at it: <a href="https://www.reg.uci.edu/registrar/soc/webreg.html" target="_blank">WebReg</a></p><p>You have been removed from this watchlist; to add yourself again, please visit <a href="https://antalmanac.com" target="_blank">AntAlmanac</a> or click on <a href="{}/email/{}/{}/{}" target="_blank">this link</a></p><p>Also, was this notification correct? Were you able to add yourself? Please do let us know asap if there is anything that isn\'t working as it should be!!! <a href="https://goo.gl/forms/U8CuPs05DlIbrSfz2" target="_blank">Give (anonymous) feedback!</a></p><p>Yours sincerely,</p><p>Poor Peter\'s AntAlmanac</p></html>'.format(config.BASE_URL, code, urllib.parse.quote(names[code]), house))
            mail = Mail(from_email, subject, to_email, content)
            response = sg.client.mail.send.post(request_body=mail.get())
            content = Content("text/html",'<html><p>'+msg+'</p><p>Here\'s WebReg while we\'re at it: <a href="https://www.reg.uci.edu/registrar/soc/webreg.html" target="_blank">WebReg</a></p><p>You have been removed from this watchlist; to add yourself again, please visit <a href="https://antalmanac.com" target="_blank">AntAlmanac</a> or click on {}/email/{}/{}/{}</p><p>Also, was this notification correct? Were you able to add yourself? Please do let us know asap if there is anything that isn\'t working as it should be!!! <a href="https://goo.gl/forms/U8CuPs05DlIbrSfz2" target="_blank">Give (anonymous) feedback!</a></p><p>Yours sincerely,</p><p>Poor Peter\'s AntAlmanac</p></html>'.format(config.BASE_URL, code, urllib.parse.quote(names[code]), house))
            mail = Mail(from_email, subject, qa_email, content) #For quality assurance purposes
            response = sg.client.mail.send.post(request_body=mail.get()) #For quality assurance
            print(code)

        #send sms notifications
        print('sms')

        if aws != None:
            for num in nums[code]:
                try:
                    long_url = '{}/sms/{}/{}/{}'.format(config.BASE_URL, code, urllib.parse.quote(names[code]), num)
                    sms_msg = 'AntAlmanac: ' + msg + 'To add back to watchlist: ' + shorten(long_url)
                    print(sms_msg)
                    aws.publish(
                        PhoneNumber="+1"+num,
                        Message=sms_msg
                        )
                    subject = "[AntAlmanac Notifications] SMS CC"
                    content = Content("text/html",sms_msg)
                    mail = Mail(from_email, subject, qa_email, content) #For quality assurance purposes
                    response = sg.client.mail.send.post(request_body=mail.get()) #For quality assurance
                    print("sms")
                    print(code)
                    print(num)
                    print()
                except:
                    subject = "[AntAlmanac ERROR] SMS Hit the Fan"
                    content = Content("text/html",'SOMETHING WENT WRONG:   '+sms_msg)
                    mail = Mail(from_email, subject, qa_email, content) #For quality assurance purposes
                    response = sg.client.mail.send.post(request_body=mail.get()) #For quality assurance


        db.queue.delete_one({"code": str(code)})
