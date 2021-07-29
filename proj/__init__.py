from os import environ
from flask import Flask
from sqlalchemy import create_engine

# import blueprints to register them
from .main import homepage
from .match import match_file
from .media import media
from .report import report
from .load import finalsubmit
from .editrecords import editor



app = Flask(__name__, static_url_path='/static')
app.debug = True # remove for production


# does your application require uploaded filenames to be modified to timestamps or left as is
app.config['CORS_HEADERS'] = 'Content-Type'

app.config['MAIL_SERVER'] = '192.168.1.18'

app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB limit
app.secret_key = 'any random string'

# set the database connection string, database, and type of database we are going to point our application at
app.eng = create_engine(environ.get("DB_CONNECTION_STRING"))

app.send_from = 'admin@checker.sccwrp.org'
app.maintainers = ['robertb@sccwrp.org']

app.register_blueprint(homepage)
app.register_blueprint(match_file)
app.register_blueprint(media)
app.register_blueprint(report)
app.register_blueprint(finalsubmit)
app.register_blueprint(editor)
