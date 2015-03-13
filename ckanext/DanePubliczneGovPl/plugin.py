import mimetypes

import ckan.plugins as p
import ckan.plugins.toolkit as toolkit


class DanePubliczne(p.SingletonPlugin):
    p.implements(p.IConfigurer)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'dane_publiczne')

        mimetypes.add_type('application/json', '.geojson')



    p.implements(p.IRoutes, inherit=True)

    def before_map(self, map):
        map.connect('ckanadmin_config', '/ckan-admin/config', controller='ckanext.DanePubliczneGovPl.controllers.admin:AdminController',
                action='config', ckan_icon='check')

        map.connect('ckanadmin', '/ckan-admin/{action}', controller='ckanext.DanePubliczneGovPl.controllers.admin:AdminController')

        return map
