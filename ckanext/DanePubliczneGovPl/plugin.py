import mimetypes

import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
import ckan.lib.base as base
import paste.deploy.converters
from pylons import config

class DanePubliczne(p.SingletonPlugin):
    p.implements(p.IConfigurer)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'dane_publiczne')
        toolkit.add_resource('fanstatic', 'ckanext-reclineview')

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
        map.connect('user_dashboard_search_history', '/dashboard/search_history',
                 controller='ckanext.DanePubliczneGovPl.controllers.user:UserController', action='dashboard_search_history', ckan_icon='list')

        map.connect('group_read', '/group/{id}', controller='ckanext.DanePubliczneGovPl.controllers.group:GroupController', action='read',
                      ckan_icon='sitemap')

        return map



    p.implements(p.ITemplateHelpers)
    def get_helpers(self):
        return {'dp_check_maintenance': self.h_check_maintenance,
                'dp_if_show_gradient_with_tabs': self.h_if_show_gradient_with_tabs,
                'dp_organization_image': self.h_organization_image}

    def h_organization_image(self, org, show_placeholder_by_default = True):
        if org.get('image_display_url', None):
            return org.get('image_display_url')

        if paste.deploy.converters.asbool(config.get('dp.show_organization_placeholder_image', show_placeholder_by_default)):
            return h.url_for_static('/base/images/placeholder-organization.png')

        return None

    def h_check_maintenance(self):
        maintenance_flash = config.get('ckan.danepubliczne.maintenance_flash')

        if maintenance_flash:
            h.flash_notice(maintenance_flash)

    def h_if_show_gradient_with_tabs(self):
        return base.request.urlvars['controller'] == 'admin' \
            or (base.request.urlvars['controller'] == 'user' and base.request.urlvars['action'][:9] == 'dashboard')
