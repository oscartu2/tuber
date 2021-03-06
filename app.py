#!flask/bin/python

from flask import Flask, redirect, url_for, render_template, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from oauth import OAuthSignIn

from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map
import requests
import json
from decimal import Decimal
from math import radians, cos, sin, asin, sqrt
import os




app = Flask(__name__)
app.config['SECRET_KEY'] = '24242424'
if os.environ.has_key("DATABASE_URL"):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': '408792279458709',
        'secret': '046aa45aec64338848b150b4713f2b04'
    }
}
app.config['GOOGLEMAPS_KEY'] = "AIzaSyCZUODD2xlOWl6lb14VwG24F3n8lh2gRoI"
GoogleMaps(app)

db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'index'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)
    available = db.Column(db.Boolean, default=False)
    pending = db.Column(db.Integer, nullable=False, default=0)
    lat = db.Column(db.FLOAT, nullable=True)
    lon = db.Column(db.FLOAT, nullable=True)
    accepted = db.Column(db.Integer, nullable=False, default=0)
    accepted_name = db.Column(db.String(64))
    name = db.Column(db.String(64), nullable=True)
    major = db.Column(db.String(64), nullable=True)
    best_class = db.Column(db.String(64), nullable=True)
    tutor_wants = db.Column(db.String(64), nullable=True)

class Posts(UserMixin, db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    id_of_recipient = db.Column(db.Integer, nullable=False)
    id_of_sender = db.Column(db.Integer, nullable=False)

db.create_all()
db.session.commit()

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def index_post():
    user = load_user(current_user.id)

    name = request.form['name']
    major = request.form['major']
    bestclass = request.form['bestclass']
    wanttutors = request.form['wanttutors']

    user.name = name
    user.major = major
    user.best_class = bestclass
    user.tutor_wants = wanttutors
    db.session.commit()
    return redirect(url_for('userHome'))

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/userHome')
def userHome():
    return render_template('userHome.html')

@app.route('/donetutoring')
def doneTutoring():
    user = load_user(current_user.id)

    user.accepted = 0
    user.accepted_name = ""

    db.session.commit()
    return redirect(url_for('userHome'))

@app.route('/pending', methods=['GET', 'POST'])
def pending():
    posts = Posts.query.all()

    return render_template('pending.html', posts=posts)

@app.route('/api/ip/<ip_address>')
def ip(ip_address):  
    geo_data = geolocate.record_by_addr(ip_address)
    return jsonify(geo_data)


@app.route('/requestTutors')
def showRequestTutors():

    return render_template('requestTutors.html')

@app.route('/activateTutor')
def activateTutor():
    user = load_user(current_user.get_id())
    user.available = True
    db.session.commit()
    return redirect(url_for('userHome'))

@app.route('/deactivateTutor')
def deactivateTutor():
    user = load_user(current_user.get_id())
    user.available = False
    user.pending = 0

    posts = Posts.query.all()

    for indPost in posts:
        if (indPost.id_of_recipient == current_user.id):
            db.session.delete(indPost)
            

    db.session.commit()
    return redirect(url_for('userHome'))


@app.route('/signin.html')
def signIn():
    return render_template('signin.html')

@app.route('/makePost')
def makePost():
    return render_template('makePost.html')


@app.route('/showSignIn')
def showSignin():
    return render_template('signin.html')

@app.route('/firstTime')
def showFirstTime():
    return render_template('firsttime.html')

@app.route('/displayposts', methods=['POST'])
def displayposts():
    users = User.query.all()

    return render_template('displayposts.html', users=users)

@app.route('/contact/<id>')
def contact(id):
    user = load_user(id)

    counter = 1

    post = Posts(id_of_recipient = id, id_of_sender=current_user.id)

    posts = Posts.query.all()
    for indPost in posts:
        if (indPost.id_of_recipient == current_user.id):
            counter += 1



    db.session.add(post)

    user.pending = counter
    db.session.commit()
    return redirect(url_for('userHome'))

@app.route('/accept/<id>')
def accept(id):
    user = load_user(id)

    current_user.accepted = id
    current_user.accepted_name = user.name
    db.session.commit()

    return redirect(url_for('deactivateTutor'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('userHome'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('userHome'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        
        db.session.add(user)
        
        db.session.commit()
        login_user(user, True)
        return redirect(url_for('showFirstTime'))

    db.session.commit()
    login_user(user, True)
    return redirect(url_for('userHome'))
    

if __name__ == '__main__':
    app.run(debug=True)
