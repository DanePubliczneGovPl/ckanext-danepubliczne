import mimetypes

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class Layout(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'dane_publiczne')

        mimetypes.add_type('application/json', '.geojson')