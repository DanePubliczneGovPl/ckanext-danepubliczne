import mimetypes

import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h

from pylons import config

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

        map.connect('/user/register', controller='ckanext.DanePubliczneGovPl.controllers.user:UserController', action='register')
        map.connect('/user/edit', controller='ckanext.DanePubliczneGovPl.controllers.user:UserController', action='edit')
        map.connect('/user/edit/{id:.*}', controller='ckanext.DanePubliczneGovPl.controllers.user:UserController', action='edit')
        map.connect('/user/logged_in', controller='ckanext.DanePubliczneGovPl.controllers.user:UserController', action='logged_in')
        map.connect('/user/logged_out', controller='ckanext.DanePubliczneGovPl.controllers.user:UserController', action='logged_out')

        return map



    p.implements(p.ITemplateHelpers)
    def get_helpers(self):
        return {'dp_check_maintenance': self.h_check_maintenance}

    def h_check_maintenance(self):
        maintenance_flash = config.get('ckan.danepubliczne.maintenance_flash')

        if maintenance_flash:
            h.flash_notice(maintenance_flash)