from datetime import datetime
from flask_server import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5

followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id")),
)


class User(UserMixin, db.Model):
    """ The User database object model.
    
    The Flask-Login extension expects that the class used to represent users implements the following properties and methods:
        a. is_authenticated
            - This property should return True if the user is authenticated, i.e. they have provided valid credentials. (Only authenticated users will fulfill the criteria of login_required.)
        b. is_active
            - This property should return True if this is an active user - in addition to being authenticated, they also have activated their account, not been suspended, or any condition your application has for rejecting an account. Inactive accounts may not log in (without being forced of course).
        c. is_anonymous
            - This property should return True if this is an anonymous user. (Actual users should return False instead.)
        d. get_id()
            - This method must return a unicode that uniquely identifies this user, and can be used to load the user from the user_loader callback. Note that this must be a unicode - if the ID is natively an int or some other type, you will need to convert it to unicode.
        e. These are inherited from the [`UserMixin`](https://flask-login.readthedocs.io/en/latest/#flask_login.UserMixin) class.
        f. [`db.Model`](https://flask-sqlalchemy.palletsprojects.com/en/2.x/api/#models) q
    
    1. What does db.relationship() do? That function returns a new property that can do multiple things. In this case we told it to point to the Post class and load multiple of those. How does it know that this will return more than one post? Because SQLAlchemy guesses a useful default from your declaration. If you would want to have a one-to-one relationship you can pass uselist=False to relationship() (this would create a one-to-one relationship).
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    password_hash = db.Column(db.String(128))
    poster = db.Column(db.Boolean, unique=False, default=False)

    posts = db.relationship("Post", backref="author", lazy="dynamic")
    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )

    def __repr__(self):
        return "<User {}>".format(self.username)

    def set_poster(self, status):
        self.poster = status

    def is_poster(self):
        return self.poster

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return "https://www.gravatar.com/avatar/{}?d=identicon&s={}".format(
            digest, size
        )

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() == 1

    def followers(self):
        follower_posts = (
            Post.query.join(followers, (followers.c.follower_id == Post.user_id))
            .filter(followers.c.followed_id == self.id)
            .all()
        )

        return set(
            [User.query.filter_by(id=post.user_id).first() for post in follower_posts]
        )

    def followed_users(self):
        followed = (
            Post.query.join(followers, (followers.c.followed_id == Post.user_id))
            .filter(followers.c.follower_id == self.id)
            .all()
        )

        return set([User.query.filter_by(id=post.user_id).first() for post in followed])

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)
        ).filter(followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())


@login.user_loader
def load_user(id):
    """ This function is the glue between Flask-Login and the remote SQL database.
    
    """
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(140))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return "<Post {}>".format(self.url)
