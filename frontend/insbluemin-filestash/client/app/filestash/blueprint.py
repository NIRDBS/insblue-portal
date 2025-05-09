from insbluemin.core.blueprints import *
from .views import *


class Filestash(RenderBlueprint):
    url_prefix = '/'
    static_url_path = '/assets'

    def register_views(self):
        self.add_view(FilestashView)
