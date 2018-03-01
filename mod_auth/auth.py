import random
import string
import json
import httplib2
import requests
from flask import Flask, render_template, request
from flask import redirect, url_for, flash
from flask import session as login_session
from flask import make_response, Blueprint
from oauth2client import client
from db_setup import User
from mod_db.connect_db import connect_db

auth = Blueprint('mod_auth', __name__, template_folder='templates')

CLIENT_ID = json.loads(open(
    'g_client_secrets.json', 'r').read())['web']['client_id']

session = connect_db()


@auth.route('/login')
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


@auth.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Connect using Google API
    """
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-type'] = 'modlication/json'
        return response
    # one-time code
    auth_code = request.data

    """
    If this request does not have `X-Requested-With` header,
    this could be a CSRF
    """
    if not request.headers.get('X-Requested-With'):
        abort(403)

    """
    Set path to the Web modlication client_secret_*.json file you
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

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        # Send Internal Server Error back
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the acsess token is used for the intended user.
    guser_id = credentials.id_token['sub']

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
    flash('You are now logged in as %s' % login_session['username'], 'success')
    return output


@auth.route('/gdisconnect')
def gdisconnect():
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
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@auth.route('/disconnect')
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

        flash('You have successfully been logged out.', 'success')
        return redirect(url_for('mod_views.showSubjects'))


@auth.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'applicaiton/json'
        return response
    access_token = request.data

    # Exchange short-lived access token for long-lived
    app_secret = json.loads(open(
        'fb_client_secrets.json', 'r').read())['web']['app_secret']
    app_id = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_id']

    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)  # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    # Store long-lived access token to login session
    if data.get('access_token') is not None:
        login_session['access_token'] = data.get('access_token')

    token = login_session.get('access_token')

    # Use token to get user info from API
    userinfo_url = 'https://graph.facebook.com/v2.12/me?access_token=%s&fields=name,id,email' % token  # noqa
    h = httplib2.Http()
    result = h.request(userinfo_url, 'GET')[1]
    data = json.loads(result)
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']
    login_session['provider'] = 'facebook'

    # Get user picture
    url = 'https://graph.facebook.com/v2.12/me/picture?access_token=%s&redirect=0&height=200&width=200' % token  # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data['data']['url']

    # See if user exists
    user_id = getUserID(login_session['email'])
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
    flash('You are now logged in as %s' % login_session['username'], 'success')
    return output


@auth.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must be included to successfully log out
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)  # noqa
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


# Helper Methods
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
