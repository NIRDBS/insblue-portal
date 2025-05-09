from insbluemin.core.blueprints import *
from .views import *


class Forms(RenderBlueprint):
    url_prefix = '/'
    static_url_path = '/assets'

    def register_views(self):
        self.add_view(FormsView)
