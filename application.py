#!/usr/bin/env python

"""Item Catalog Project
This module does the following:
initialize the app, connect to the database, manage user login and
logout, handle routing, process data for web page views for CRUD
operations, and provide JSON endpoints
"""

import random
import string
import json
import requests
import httplib2
import datetime
from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Subject, Item, User
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import make_response
from apiclient import discovery
from oauth2client import client

app = Flask(__name__)

CLIENT_ID = json.loads(open(
    'g_client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Homework Tracker"

# Connect to Database and create database session
engine = create_engine('sqlite:///homeworkitems.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    """
    Create a state token to prevent request forgery. Store it in the session
    for later validation.
    """
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, client_id=CLIENT_ID)


def createUser(login_session):
    """
    Store login user and return its user id
    """
    newUser = User(
        name=login_session['username'], email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUser(user_id):
    """
    Return user object with the given user_id.  If no user found with
    the id, return None
    """
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user
    except:
        return None


def getUserID(email):
    """
    Return id of the user whose email matches with the given email,
    If no such user found, return None
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getSubjectName(name, user_id):
    """
    Check if a given subject name exists with the given user_id
    If no such subject found, return None
    """
    try:
        subject = session.query(Subject).filter_by(
            name=name, user_id=user_id).one()
        return subject.name
    except:
        return None


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Connect using Google API
    """
    print "gconnect!"
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-type'] = 'application/json'
        return response
    # one-time code
    auth_code = request.data
    print "one time code received"

    """
    If this request does not have `X-Requested-With` header,
    this could be a CSRF
    """
    if not request.headers.get('X-Requested-With'):
        abort(403)

    """
    Set path to the Web application client_secret_*.json file you
    downloaded from the Google API Console:
    https://console.developers.google.com/apis/credentials
    """
    CLIENT_SECRET_FILE = 'g_client_secrets.json'

    # Exchange auth code for access token, refresh token, and ID token
    credentials = client.credentials_from_clientsecrets_and_code(
        CLIENT_SECRET_FILE,
        ['https://www.googleapis.com/auth/drive.appdata', 'profile', 'email'],
        auth_code)

    # Check that the access token is valid
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    print result

    print 'access_token: %s' % access_token
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        # Send Internal Server Error back
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the acsess token is used for the intended user.
    guser_id = credentials.id_token['sub']
    print 'guser_id: %s' % guser_id
    print 'login session guser %s' % login_session.get('guser_id')
    if result['user_id'] != guser_id:
        # Send Unauthorized status code back
        response = make_response(json.dumps(
            "Token's user info ID does not match given user ID"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    # gplus_id = credentials.id_token['sub']
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            "Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later used
    login_session['access_token'] = credentials.access_token
    login_session['guser_id'] = guser_id
    login_session['provider'] = "google"

    # Get user Info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if user exisits, if it doesn't, create a new user
    user_id = getUserID(login_session['email'])
    print "%s returned with %s " % (user_id, login_session['email'])
    if user_id is None:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style="width: 200px; height: 200px; border-radius: 50%;">'
    flash("You are now logged in as %s" % login_session['username'])
    return output


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['guser_id']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        del login_session['access_token']

        flash('You have successfully been logged out.')
        return redirect(url_for('showSubjects'))


@app.route('/gdisconnect')
def gdisconnect():
    print("gdisconnect")
    # Execute HTTP GET request to revoke current token
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        print ("successfuly disconnected")
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    print 'fbconnect'
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'applicaiton/json'
        return response
    access_token = request.data
    print "access_token %s" % access_token

    # Exchange short-lived access token for long-lived
    app_secret = json.loads(open(
        'fb_client_secrets.json', 'r').read())['web']['app_secret']
    app_id = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_id']
    print 'appid %s' % app_id
    print 'app_secret %s' % app_secret
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)  # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    print 'result %s' % result
    data = json.loads(result)

    # Store long-lived access token to login session
    if data.get('access_token') is not None:
        print data.get('access_token')
        login_session['access_token'] = data.get('access_token')

    token = login_session.get('access_token')

    # Use token to get user info from API
    userinfo_url = 'https://graph.facebook.com/v2.12/me?access_token=%s&fields=name,id,email' % token  # noqa
    h = httplib2.Http()
    result = h.request(userinfo_url, 'GET')[1]
    print 'user info result %s' % result
    data = json.loads(result)
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']
    login_session['provider'] = 'facebook'

    # Get user picture
    url = 'https://graph.facebook.com/v2.12/me/picture?access_token=%s&redirect=0&height=200&width=200' % token  # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    print 'picture result %s' % result
    data = json.loads(result)

    login_session['picture'] = data['data']['url']

    # See if user exists
    user_id = getUserID(login_session['email'])
    print "user_id %s " % user_id
    if user_id is None:
        print "########creat user now##########"
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style="width: 200px; height: 200px; border-radius: 50%;">'
    flash("You are now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must be included to successfully log out
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)  # noqa
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


# JSON APIs to view Subject Information
@app.route('/subject/<int:subject_id>/item/JSON')
def homeworkItemsJSON(subject_id):
    subject = session.query(Subject).filter_by(id=subject_id).one()
    items = session.query(Item).filter_by(subject_id=subject_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/subject/<int:subject_id>/item/<int:item_id>/JSON')
def homeworkItemJSON(subject_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


@app.route('/subject/JSON')
def subjectsJSON():
    subjects = session.query(Subject).all()
    return jsonify(subjects=[s.serialize for s in subjects])


@app.route('/')
@app.route('/subject/')
def showSubjects():
    """
    Show all subjects stored in the database
    """
    subjects = session.query(Subject).order_by(asc(Subject.name))
    subject_creator = []
    for subject in subjects:
        timestamp = subject.timestamp
        user = getUser(subject.user_id)
        card_info = (subject, user, timestamp)
        subject_creator.append(card_info)
    if 'username' not in login_session:
        return render_template('publicsubjects.html', subjects=subject_creator)
    else:
        picture = login_session['picture']
        return render_template(
            'subjects.html', subjects=subject_creator, picture=picture)


@app.route('/subject/new/', methods=['GET', 'POST'])
def newSubject():
    """
    Create a new subject
    """
    if 'username' not in login_session:
        return redirect('/login')

    picture = login_session['picture']

    if request.method == 'POST':

        # Subject name cannot be empty
        if request.form['name'] == "":
            print("subject name is empty")
            flash('Please enter a subject name.', 'error')
            return render_template('new_subject.html', picture=picture)
        # Check if subject name already exists with this user
        subjectName = getSubjectName(
            request.form['name'], login_session['user_id'])
        if subjectName == request.form['name']:
            print("subject name already exists")
            flash(
                "%s already exists. Please enter a different subject name."
                % request.form['name'], 'error')
            return redirect('/subject/new/', picture=picture)
        else:
            newSubject = Subject(
                name=request.form['name'], user_id=login_session['user_id'])
            session.add(newSubject)
            flash('New subject \'%s\' successfully created!' % newSubject.name)
            session.commit()
            return redirect(url_for('showSubjects'))
    else:
        return render_template('new_subject.html', picture=picture)


@app.route('/subject/<int:subject_id>/edit/', methods=['GET', 'POST'])
def editSubject(subject_id):
    """
    Edit a subject
    """
    if 'username' not in login_session:
        return redirect('/login')
    editedSubject = session.query(Subject).filter_by(id=subject_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedSubject.name = request.form['name']
            flash('\'%s\' successfully edited ' % editedSubject.name)
            return redirect(url_for('showSubjects'))
    else:
        picture = login_session['picture']
        return render_template(
            'edit_subject.html', subject=editedSubject, picture=picture)


@app.route('/subject/<int:subject_id>/delete/', methods=['GET', 'POST'])
def deleteSubject(subject_id):
    """
    Delete a subject
    """
    subjectToDelete = session.query(Subject).filter_by(id=subject_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        session.delete(subjectToDelete)
        flash('\'%s\' successfully deleted' % subjectToDelete.name)
        session.commit()
        return redirect(url_for('showSubjects', subject_id=subject_id))
    else:
        picture = login_session['picture']
        return render_template(
            'delete_subject.html', subject=subjectToDelete, picture=picture)


@app.route('/subject/<int:subject_id>/')
@app.route('/subject/<int:subject_id>/item/')
def showItems(subject_id):
    """
    Show homework items for each subject
    """
    subject = session.query(Subject).filter_by(id=subject_id).one()
    creator = getUser(subject.user_id)
    items = session.query(Item).filter_by(subject_id=subject_id).all()

    if 'username' not in login_session:
        return render_template(
            'publicitems.html', items=items, subject=subject)
    else:
        # Get picture of current user
        picture = login_session['picture']
        if creator.id != login_session['user_id']:
            return render_template(
                'publicitems.html', items=items, subject=subject,
                picture=picture)
        else:
            items = session.query(Item).filter_by(subject_id=subject_id).all()
            return render_template(
                'items.html', items=items, subject=subject, picture=picture)


@app.route('/subject/<int:subject_id>/item/new/', methods=['GET', 'POST'])
def newItem(subject_id):
    """
    Create a new homework item
    """
    if 'username' not in login_session:
        return redirect('/login')
    subject = session.query(Subject).filter_by(id=subject_id).one()
    if request.method == 'POST':
        if request.form['name'] == "":
            print("Item name is empty.")
            flash("Please enter an item name.", 'error')
            return redirect(url_for('newItem', subject_id=subject_id))
        newItem = Item(
            name=request.form['name'], description=request.form['description'],
            time_estimate=request.form['time_estimate'],
            priority=request.form['priority'], subject_id=subject_id,
            user_id=subject.user_id)
        session.add(newItem)
        session.commit()
        flash('\'%s\' successfully created' % (newItem.name))
        return redirect(url_for('showItems', subject_id=subject_id))
    else:
        picture = login_session['picture']
        return render_template(
            'new_item.html', subject_id=subject_id, picture=picture)


@app.route(
    '/subject/<int:subject_id>/item/<int:item_id>/edit',
    methods=['GET', 'POST'])
def editItem(subject_id, item_id):
    """
    Edit a homework item
    """
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Item).filter_by(id=item_id).one()
    subject = session.query(Subject).filter_by(id=subject_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['time_estimate']:
            editedItem.time_estimate = request.form['time_estimate']
        if request.form['priority']:
            editedItem.priority = request.form['priority']
        session.add(editedItem)
        session.commit()
        flash('\'%s\' successfully edited' % request.form['name'])
        return redirect(url_for('showItems', subject_id=subject_id))
    else:
        picture = login_session['picture']
        return render_template(
            'edit_item.html', subject_id=subject_id, item_id=item_id,
            item=editedItem, picture=picture)


@app.route(
    '/subject/<int:subject_id>/item/<int:item_id>/delete',
    methods=['GET', 'POST'])
def deleteItem(subject_id, item_id):
    """
    Delete a homework item
    """
    if 'username' not in login_session:
        return redirect('/login')
    subject = session.query(Subject).filter_by(id=subject_id).one()
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    itemName = itemToDelete.name
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('\'%s\' successfully deleted' % itemName)
        return redirect(url_for('showItems', subject_id=subject_id))
    else:
        picture = login_session['picture']
        return render_template(
            'delete_item.html', subject_id=subject_id, item=itemToDelete,
            picture=picture)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
