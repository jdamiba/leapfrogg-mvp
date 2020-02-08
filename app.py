from flask_server import flask_server, db
from flask_server.models import User, Post


@flask_server.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Post": Post}
