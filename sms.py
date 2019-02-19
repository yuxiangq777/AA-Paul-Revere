# Download the helper library from https://www.twilio.com/docs/python/install
from twilio.rest import Client
import config

# Your Account Sid and Auth Token from twilio.com/console
account_sid = config.account_sid
auth_token = config.auth_token
client = Client(account_sid, auth_token)

message = client.messages.create(from_=config.from_number, body='AntAlamanc sending sms',to=config.to)
print(message.sid)