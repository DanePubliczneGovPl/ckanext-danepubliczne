import mimetypes
import sys
import logging

import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
import ckan.lib.base as base
import ckan.lib.activity_streams as activity_streams
import ckan.new_authz as new_authz
import ckan.logic
import ckan.model as model
from ckan.common import _
from webhelpers.html import literal
import paste.deploy.converters
from pylons import config
from pylons.util import class_name_from_module_name
from routes.mapper import SubMapper
import ckan.lib.app_globals as app_globals


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


        # don't show user names in activity stream
        def get_snippet_actor_org(activity, detail):
            return literal('''<span class="actor">%s</span>'''
                           % (linked_org_for(activity['user_id'], 0, 30))
                           )

        activity_streams.activity_snippet_functions['actor'] = get_snippet_actor_org


    p.implements(p.IMiddleware, inherit=True)

    def make_middleware(self, app, config):
        # Hack it so our controllers pretend they are original ones! Buahahhaha!
        overriden_controlers = ['package', 'user', 'admin', 'group', 'organization']

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
            m.connect('user_dashboard_account', '/dashboard/account',
                      action='read', ckan_icon='user_grey')

        with SubMapper(map, controller='package') as m:
            m.connect('dataset_search', '/dataset', action='search',
                      highlight_actions='index search')

        map.connect('data_feedback_submit', '/feedback_data',
                    controller='ckanext.danepubliczne.controllers.feedback:FeedbackController', action='data_feedback')
        map.connect('new_dataset_feedback_submit', '/new_dataset_feedback',
                    controller='ckanext.danepubliczne.controllers.feedback:FeedbackController',
                    action='new_dataset_feedback')

        with SubMapper(map, controller='ckanext.danepubliczne.controllers.api:UtilExtension',
                       path_prefix='/api{ver:/1|/2|}',
                       ver='/1') as m:
            m.connect('/util/user/autocomplete_email', action='user_autocomplete_email')

        return map


    p.implements(p.ITemplateHelpers)

    def get_helpers(self):
        return {'dp_check_maintenance': self.h_check_maintenance,
                'dp_if_show_gradient_with_tabs': self.h_if_show_gradient_with_tabs,
                'dp_organization_image': self.h_organization_image}

    def h_organization_image(self, org, show_placeholder_by_default=True):
        if org.get('image_display_url', None):
            return org.get('image_display_url')

        if paste.deploy.converters.asbool(
                config.get('dp.show_organization_placeholder_image', show_placeholder_by_default)):
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


    p.implements(p.IActions)

    def get_actions(self):
        return {
            'user_autocomplete_email': user_autocomplete_email,
            'member_list': member_list
        }


    p.implements(p.IAuthFunctions)

    def get_auth_functions(self):
        return {
            # Only sysadmins can list users
            'user_list': ckan.logic.auth.get.sysadmin,
            'member_list': ckan.logic.auth.get.sysadmin,
            'user_show': auth_user_show
        }


@ckan.logic.validate(ckan.logic.schema.default_autocomplete_schema)
def user_autocomplete_email(context, data_dict):
    '''Return a list of user names that contain a string.

    :param q: the string to search for
    :type q: string
    :param limit: the maximum number of user names to return (optional,
        default: 20)
    :type limit: int

    :rtype: a list of user dictionaries each with keys ``'name'``,
        ``'fullname'``, and ``'id'``

    '''
    model = context['model']
    user = context['user']

    ckan.logic.check_access('user_autocomplete', context, data_dict)

    q = data_dict['q']
    limit = data_dict.get('limit', 20)

    query = model.User.search(q, user_name=user)
    query = query.filter(model.User.state != model.State.DELETED)
    query = query.limit(limit)

    user_list = []
    for user in query.all():
        result_dict = {}
        for k in ['id', 'name', 'fullname', 'email']:
            result_dict[k] = getattr(user, k)

        result_dict['fullname_with_email'] = "%s &lt;%s&gt;" % (user.fullname or '', user.email)

        user_list.append(result_dict)

    return user_list


# Only sysadmins can list members
def member_list(context, data_dict=None):
    '''Return the members of a group.

    The user must have permission to 'get' the group.

    :param id: the id or name of the group
    :type id: string
    :param object_type: restrict the members returned to those of a given type,
      e.g. ``'user'`` or ``'package'`` (optional, default: ``None``)
    :type object_type: string
    :param capacity: restrict the members returned to those with a given
      capacity, e.g. ``'member'``, ``'editor'``, ``'admin'``, ``'public'``,
      ``'private'`` (optional, default: ``None``)
    :type capacity: string

    :rtype: list of (id, type, capacity) tuples

    :raises: :class:`ckan.logic.NotFound`: if the group doesn't exist

    '''
    model = context['model']

    group = model.Group.get(ckan.logic.get_or_bust(data_dict, 'id'))
    if not group:
        raise ckan.logic.NotFound

    obj_type = data_dict.get('object_type', None)
    capacity = data_dict.get('capacity', None)

    ckan.logic.check_access('member_list', context, data_dict)

    q = model.Session.query(model.Member). \
        filter(model.Member.group_id == group.id). \
        filter(model.Member.state == "active")

    if obj_type:
        q = q.filter(model.Member.table_name == obj_type)
    if capacity:
        q = q.filter(model.Member.capacity == capacity)

    trans = new_authz.roles_trans()

    def translated_capacity(capacity):
        try:
            return trans[capacity]
        except KeyError:
            return capacity

    return [(m.table_id, m.table_name, translated_capacity(m.capacity))
            for m in q.all()]


def auth_user_show(context, data_dict):
    # Allow users to only see their profiles
    success = False
    if data_dict.get('id'):
        success = context['user'] == data_dict['id']
    elif data_dict.get('user_obj'):
        success = context['user'] == data_dict['user_obj'].name

    return {'success': success}


def linked_org_for(user, maxlength=0, avatar=20):
    if user in [model.PSEUDO_USER__LOGGED_IN, model.PSEUDO_USER__VISITOR]:
        return user
    if not isinstance(user, model.User):
        user_name = unicode(user)
        user = model.User.get(user_name)
        if not user:
            return user_name

    if user:
        groups = user.get_groups('organization')
        if not groups or len(groups) > 1:
            return user.name if model.User.VALID_NAME.match(user.name) else user.id

        org = groups[0]  # Assuming user only in one org
        displayname = org.display_name
        if maxlength and len(displayname) > maxlength:
            displayname = displayname[:maxlength] + '...'
        return h.link_to(displayname, h.url_for(controller='organization', action='read', id=org.name))