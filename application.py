#!/usr/bin/env python

"""
This module registers blueprints and initializes the Flask web app
"""

from flask import Flask
from mod_auth.auth import auth
from mod_views.views import views
from mod_api.api import api
from mod_db.connect_db import db

app = Flask(__name__)

if __name__ == '__main__':
    app.register_blueprint(auth)
    app.register_blueprint(views)
    app.register_blueprint(api)
    app.register_blueprint(db)
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
