# from flask import Flask, render_template, render_template_string, jsonify, request, abort, redirect, url_for, g, \
#     current_app, session
from pocketbase import PocketBase  # Client also works the same

from insbluemin.core import CoreSettings, BlueCore, MenuBuilder, Markdown, app
from insbluemin.auth import OAuthProxyAuth
from insbluemin.utils import *
from insbluemin.core.logger import log

from werkzeug.middleware.proxy_fix import ProxyFix


class ModuleSettings(CoreSettings):
    FORMIO_API_URL: str = ...
    FORMIO_API_KEY: str = ...
    FORMIO_API_SECRET: str = ...

    HASHIDS_SALT: str = ...
    HASHIDS_ALPHABET: str = ...


app.config['APP_DIR'] = os.path.dirname(__file__)
app.config['APPLICATION_ROOT'] = '/forms/'  # this needs to be commented out for localhost development else the login loops
# app.config['SERVER_NAME'] = 'insblue.incdsb.ro'

module_settings = ModuleSettings()
app.config.from_object(module_settings)

app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

log.setLevel(logging.INFO)

Markdown(app)

auth_manager = OAuthProxyAuth(app, 'login')
pb = PocketBase(app.config.get("POCKETBASE_URL"))
BlueCore(app, db=pb, auth_manager=auth_manager, default_view='Forms.index')

MenuBuilder(app)

if __name__ == '__main__':
    app.run(debug=False, port=5000, host="192.168.0.178")  # 192.168.1.186
