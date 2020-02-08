from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required
from config import Config

flask_server = Flask(__name__, static_folder="static")
flask_server.config.from_object(Config)
db = SQLAlchemy(flask_server)
migrate = Migrate(flask_server, db)
login = LoginManager(flask_server)
login.login_view = "login"

from flask_server import routes, models, errors
