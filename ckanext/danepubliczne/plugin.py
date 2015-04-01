import mimetypes

import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
import ckan.lib.base as base
import paste.deploy.converters
from pylons import config
from pylons.util import class_name_from_module_name
from routes.mapper import SubMapper
import ckan.lib.app_globals as app_globals
from ckan.common import _
import sys, logging

log = logging.getLogger(__name__)

class DanePubliczne(p.SingletonPlugin):
    p.implements(p.IConfigurer)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'dane_publiczne')
        toolkit.add_resource('fanstatic', 'ckanext-reclineview')

        mimetypes.add_type('application/json', '.geojson')

        # TODO ckan-dev load all properties from SystemInfo at load, instead of using app_globals.auto_update:
        # TODO ckan-dev def get_globals_key(key):   should allow ckanext.
        app_globals.auto_update += [
            'ckanext.danepubliczne.maintenance_flash',
        ]
        for locale in h.get_available_locales():
            lang = locale.language
            app_globals.auto_update += ['ckan.site_intro_text-' + lang, 'ckan.site_about-' + lang]



    p.implements(p.IMiddleware, inherit=True)
    def make_middleware(self, app, config):
        # Hack it so our controllers pretend they are original ones! Buahahhaha!
        overriden_controlers = ['package', 'user', 'admin', 'group']

        for controller in overriden_controlers:
            # Pull the controllers class name, import controller
            full_module_name = 'ckanext.danepubliczne.controllers.' \
                + controller.replace('/', '.')

            # Hide the traceback here if the import fails (bad syntax and such)
            __traceback_hide__ = 'before_and_this'

            __import__(full_module_name)
            if hasattr(sys.modules[full_module_name], '__controller__'):
                mycontroller = getattr(sys.modules[full_module_name],
                    sys.modules[full_module_name].__controller__)
            else:
                module_name = controller.split('/')[-1]
                class_name = class_name_from_module_name(module_name) + 'Controller'
                if app.log_debug:
                    log.debug("Found controller, module: '%s', class: '%s'",
                              full_module_name, class_name)
                mycontroller = getattr(sys.modules[full_module_name], class_name)

            app.controller_classes[controller] = mycontroller

        return app



    p.implements(p.IRoutes, inherit=True)

    def before_map(self, map):
        map.connect('ckanadmin_config', '/ckan-admin/config', controller='admin', action='config', ckan_icon='check')
        map.connect('qa_index', '/qa', controller='ckanext.qa.controller:QAController', action='index')

        with SubMapper(map, controller='ckanext.danepubliczne.controllers.user:UserController') as m:
            m.connect('user_dashboard_search_history', '/dashboard/search_history',
                     action='dashboard_search_history', ckan_icon='list')

        map.connect('data_feedback_submit', '/feedback_data', controller='ckanext.danepubliczne.controllers.feedback:FeedbackController', action='data_feedback')
        map.connect('new_dataset_feedback_submit', '/new_dataset_feedback', controller='ckanext.danepubliczne.controllers.feedback:FeedbackController', action='new_dataset_feedback')

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
        maintenance_flash = config.get('ckanext.danepubliczne.maintenance_flash')

        if maintenance_flash:
            h.flash_notice(maintenance_flash)

    def h_if_show_gradient_with_tabs(self):
        return base.request.urlvars['controller'] == 'admin' \
            or (base.request.urlvars['controller'] == 'user' and base.request.urlvars['action'][:9] == 'dashboard')

    # TODO ckan-dev What is the preferred way to make multilingual groups / datasets /tags: fluent or multilingual?


    p.implements(p.IAuthenticator, inherit=True)
    def login(self):
        h.flash_notice(_('We use cookies to handle logged-in users'))
