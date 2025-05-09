from flask import render_template, session, current_app
from insbluemin.core.views import *
from insbluemin.core.decorators import *
from insbluemin.core.auth_manager import current_user
import requests


class FilestashView(BaseView):
    default_view = 'index'

    def __init__(self, app, menu):
        print('Loaded Filestash module')
        super().__init__(app, menu)

    @add_to_menu(location='sidebar', group='Intranet', parent='Intranet:fa-solid fa-file-lines', label='Intranet', icon='fa-solid fa-file')
    @has_permissions(['core.can_view'])
    @expose('/', methods=['GET'])
    def index(self):
        iframe_src = '//files.incdsb.ro/'
        if request.args.get('loc'):
            iframe_src = iframe_src + request.args.get('loc')

        return self.render_template('filestash.jinja2', iframe_src=iframe_src)

    @has_permissions(['core.can_view'])
    @expose('/view/<view_path>', methods=['GET'])
    def view_path(self, view_path):
        iframe_src = '//files.incdsb.ro/'
        iframe_src = iframe_src + 'view/' + view_path

        return self.render_template('filestash.jinja2', iframe_src=iframe_src)

    # MAJOR HACK because i con't be arsed to recompile filestash right now
    # @todo: recompile filestash with proper .js url
    @has_permissions(['core.can_view'])
    @expose('/static/dist/js/insblu.js', methods=['GET'])
    def serve_insblu_js(self):
        return redirect('/assets/dist/js/insblu.js', code=301)
