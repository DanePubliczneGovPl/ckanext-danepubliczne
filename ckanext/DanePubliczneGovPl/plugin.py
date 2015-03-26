import mimetypes

import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
import ckan.lib.base as base
import paste.deploy.converters
from pylons import config
from routes.mapper import SubMapper

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

        with SubMapper(map, controller='ckanext.DanePubliczneGovPl.controllers.group:GroupController') as m:
            m.connect('group_index', '/group', action='index',
                      highlight_actions='index search')
            m.connect('group_list', '/group/list', action='list')
            m.connect('group_new', '/group/new', action='new')
            m.connect('group_action', '/group/{action}/{id}',
                      requirements=dict(action='|'.join([
                          'edit',
                          'delete',
                          'member_new',
                          'member_delete',
                          'history',
                          'followers',
                          'follow',
                          'unfollow',
                          'admins',
                          'activity',
                      ])))
            m.connect('group_about', '/group/about/{id}', action='about',
                      ckan_icon='info-sign'),
            m.connect('group_edit', '/group/edit/{id}', action='edit',
                      ckan_icon='edit')
            m.connect('group_members', '/group/members/{id}', action='members',
                      ckan_icon='group'),
            m.connect('group_activity', '/group/activity/{id}/{offset}',
                      action='activity', ckan_icon='time'),
            m.connect('group_read', '/group/{id}', action='read',
                      ckan_icon='sitemap')

        # TODO ckan-dev ability to override controller from config
        with SubMapper(map, controller='ckanext.DanePubliczneGovPl.controllers.package:PackageController') as m:
            m.connect('search', '/dataset', action='search',
                      highlight_actions='index search')
            m.connect('add dataset', '/dataset/new', action='new')
            m.connect('/dataset/{action}',
                      requirements=dict(action='|'.join([
                          'list',
                          'autocomplete',
                          'search'
                      ])))

            m.connect('/dataset/{action}/{id}/{revision}', action='read_ajax',
                      requirements=dict(action='|'.join([
                          'read',
                          'edit',
                          'history',
                      ])))
            m.connect('/dataset/{action}/{id}',
                      requirements=dict(action='|'.join([
                          'new_metadata',
                          'new_resource',
                          'history',
                          'read_ajax',
                          'history_ajax',
                          'follow',
                          'activity',
                          'groups',
                          'unfollow',
                          'delete',
                          'api_data',
                      ])))
            m.connect('dataset_edit', '/dataset/edit/{id}', action='edit',
                      ckan_icon='edit')
            m.connect('dataset_followers', '/dataset/followers/{id}',
                      action='followers', ckan_icon='group')
            m.connect('dataset_activity', '/dataset/activity/{id}',
                      action='activity', ckan_icon='time')
            m.connect('/dataset/activity/{id}/{offset}', action='activity')
            m.connect('dataset_groups', '/dataset/groups/{id}',
                      action='groups', ckan_icon='group')
            m.connect('/dataset/{id}.{format}', action='read')
            m.connect('dataset_resources', '/dataset/resources/{id}',
                      action='resources', ckan_icon='reorder')
            m.connect('dataset_read', '/dataset/{id}', action='read',
                      ckan_icon='sitemap')
            m.connect('/dataset/{id}/resource/{resource_id}',
                      action='resource_read')
            m.connect('/dataset/{id}/resource_delete/{resource_id}',
                      action='resource_delete')
            m.connect('resource_edit', '/dataset/{id}/resource_edit/{resource_id}',
                      action='resource_edit', ckan_icon='edit')
            m.connect('/dataset/{id}/resource/{resource_id}/download',
                      action='resource_download')
            m.connect('/dataset/{id}/resource/{resource_id}/download/{filename}',
                      action='resource_download')
            m.connect('/dataset/{id}/resource/{resource_id}/embed',
                      action='resource_embedded_dataviewer')
            m.connect('/dataset/{id}/resource/{resource_id}/viewer',
                      action='resource_embedded_dataviewer', width="960",
                      height="800")
            m.connect('/dataset/{id}/resource/{resource_id}/preview',
                      action='resource_datapreview')
            m.connect('views', '/dataset/{id}/resource/{resource_id}/views',
                      action='resource_views', ckan_icon='reorder')
            m.connect('new_view', '/dataset/{id}/resource/{resource_id}/new_view',
                      action='edit_view', ckan_icon='edit')
            m.connect('edit_view',
                      '/dataset/{id}/resource/{resource_id}/edit_view/{view_id}',
                      action='edit_view', ckan_icon='edit')
            m.connect('resource_view',
                      '/dataset/{id}/resource/{resource_id}/view/{view_id}',
                      action='resource_view')
            m.connect('/dataset/{id}/resource/{resource_id}/view/',
                      action='resource_view')

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
