import uuid

DEBUG = False
TESTING = False
SECRET_KEY = str(uuid.uuid4())
USERNAME = str(uuid.uuid4())
PASSWORD = str(uuid.uuid4())

NAME = 'datapusher'

# database

SQLALCHEMY_DATABASE_URI = 'sqlite:////home/ckan/data/datapusher.db'

# webserver host and port

HOST = '127.0.0.1'
PORT = 8800

# logging

# FROM_EMAIL = 'server-error@example.com'
#ADMINS = ['yourname@example.com']  # where to send emails

LOG_FILE = '/var/log/ckan/datapusher.log'
STDERR = True
