from flask import Flask, render_template, render_template_string, jsonify, request, abort, redirect, url_for, g, \
    current_app, session
from pocketbase import PocketBase  # Client also works the same

from insbluemin.core import BlueCore
from insbluemin.core import MenuBuilder
from insbluemin.auth import OAuthProxyAuth
from insbluemin.utils import *
from insbluemin.core import app
from insbluemin.core import Markdown
from insbluemin.core.logger import log

from werkzeug.middleware.proxy_fix import ProxyFix

app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

app.config["POCKETBASE_URL"] = "https://api.incdsb.ro/pb/"
# app.config["POCKETBASE_URL"] = "http://192.168.240.4:8090/"

app.config['APP_DIR'] = os.path.dirname(__file__)
# app.config['SERVER_NAME'] = 'insblue.incdsb.ro'
# app.config['APPLICATION_ROOT'] = '/files/'  # this needs to be commented out for localhost development else the login loops

log.setLevel(logging.INFO)
# app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

"""
    Might require more work depending on how the use case evolves. Atm PocketbaseJWT/Auth handles the auth process 
    between Core and Pocketbase server using flask-jwt-extended as an intermediary
"""

Markdown(app)

auth_manager = OAuthProxyAuth(app, 'login')
pb = PocketBase(app.config.get("POCKETBASE_URL"))
BlueCore(app, db=pb, auth_manager=auth_manager, default_view='Filestash.index')

MenuBuilder(app)

if __name__ == '__main__':
    app.run(debug=False, port=5000, host="192.168.0.178")
