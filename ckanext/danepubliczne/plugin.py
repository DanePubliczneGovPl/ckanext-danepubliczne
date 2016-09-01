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
import ckan.lib.dictization.model_dictize as model_dictize

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
        overriden_controlers = ['package', 'user', 'admin', 'group', 'organization', 'home']

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
        map.connect('sitemap', '/sitemap', controller='ckanext.danepubliczne.controllers.home:HomeController', action='sitemap')
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
            m.connect('jupload_resource', '/dataset/jupload_resource/{id}', action='jupload_resource')
            m.connect('download', '/dataset/download', action='download')

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

    def after_map(self, map):
        with SubMapper(map, controller='organization') as m:
            m.connect('organizations_index', '/organization', action='index new read')
        return map

    p.implements(p.ITemplateHelpers)

    def get_helpers(self):
        return {'dp_check_maintenance': self.h_check_maintenance,
                'dp_if_show_gradient_with_tabs': self.h_if_show_gradient_with_tabs,
                'dp_organization_image': self.h_organization_image,
                'dp_get_facet_items_dict_sortable': self.h_get_facet_items_dict_sortable,
                'add_url_param_unique': self.h_add_url_param_unique}

    @classmethod
    def h_add_url_param_unique(self, alternative_url=None, controller=None, action=None, extras=None, new_params=None):
        from ckan.common import request
        from ckan.lib import helpers as h
        log.warn(new_params)
        params_nopage = [(k, v) for k, v in request.params.items() if ((k != 'page') and (k not in new_params))]
        params = set(params_nopage)
        if new_params:
            params |= set(new_params.items())
        if alternative_url:
            return h._url_with_params(alternative_url, params)
        return h._create_url_with_params(params=params, controller=controller, action=action, extras=extras)
    
    @classmethod
    def h_get_facet_items_dict_sortable(self, facet, limit=None, exclude_active=False):
        ''' code for this function is copied from lib/helpers.py get_facet_items_dict function
        exepct it allows custom facets sorting '''

        from ckan.common import request, c

        sort_field = 'name' if (facet == 'res_extras_openness_score') else 'count'

        if not c.search_facets or \
                not c.search_facets.get(facet) or \
                not c.search_facets.get(facet).get('items'):
            return []
        facets = []
        for facet_item in c.search_facets.get(facet)['items']:
            if not len(facet_item['name'].strip()):
                continue
            if not (facet, facet_item['name']) in request.params.items():
                facets.append(dict(active=False, **facet_item))
            elif not exclude_active:
                facets.append(dict(active=True, **facet_item))
        facets = sorted(facets, key=lambda item: item[sort_field], reverse=True)
        if c.search_facets_limits and limit is None:
            limit = c.search_facets_limits.get(facet)
        # zero treated as infinite for hysterical raisins
        if limit is not None and limit > 0:
            return facets[:limit]
        return facets

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


    p.implements(p.IActions)

    def get_actions(self):
        return {
            'user_autocomplete_email': user_autocomplete_email,
            'member_list': member_list,
        }


    p.implements(p.IAuthFunctions)

    def get_auth_functions(self):
        return {
            # Only sysadmins can list users and create related items
            'user_list': ckan.logic.auth.get.sysadmin,
            'member_list': ckan.logic.auth.get.sysadmin,
            'related_create': ckan.logic.auth.get.sysadmin,
            'user_show': auth_user_show,
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

def _group_or_org_list_filtered(context, data_dict, is_org=False):

    from paste.deploy.converters import asbool
    import ckan.lib.dictization.model_dictize as model_dictize
    import sqlalchemy

    model = context['model']
    api = context.get('api_version')
    groups = data_dict.get('groups')
    group_type = data_dict.get('type', 'group')
    ref_group_by = 'id' if api == 2 else 'name'

    sort = data_dict.get('sort', 'name')
    q = data_dict.get('q')
    extra_conditions = data_dict.get('extra_conditions')

    # order_by deprecated in ckan 1.8
    # if it is supplied and sort isn't use order_by and raise a warning
    order_by = data_dict.get('order_by', '')
    if order_by:
        log.warn('`order_by` deprecated please use `sort`')
        if not data_dict.get('sort'):
            sort = order_by
    # if the sort is packages and no sort direction is supplied we want to do a
    # reverse sort to maintain compatibility.
    if sort.strip() in ('packages', 'package_count'):
        sort = 'package_count desc'

    sort_info = ckan.logic.action.get._unpick_search(sort,
                               allowed_fields=['name', 'packages',
                                               'package_count', 'title'],
                               total=1)

    all_fields = data_dict.get('all_fields', None)
    include_extras = all_fields and \
                     asbool(data_dict.get('include_extras', False))

    query = model.Session.query(model.Group)
    if include_extras:
        # this does an eager load of the extras, avoiding an sql query every
        # time group_list_dictize accesses a group's extra.
        query = query.options(sqlalchemy.orm.joinedload(model.Group._extras))
    query = query.filter(model.Group.state == 'active')
    if groups:
        query = query.filter(model.Group.name.in_(groups))
    if q:
        q = u'%{0}%'.format(q)
        query = query.filter(sqlalchemy.or_(
            model.Group.name.ilike(q),
            model.Group.title.ilike(q),
            model.Group.description.ilike(q),
        ))

    if extra_conditions:
        query = query.join(model.GroupExtra)
        for cond in extra_conditions:
            if cond[1] == '==':
                query = query.filter(model.GroupExtra.key == cond[0], model.GroupExtra.value == cond[2])

    query = query.filter(model.Group.is_organization == is_org)
    if not is_org:
        query = query.filter(model.Group.type == group_type)

    groups = query.all()
    if all_fields:
        include_tags = asbool(data_dict.get('include_tags', False))
    else:
        include_tags = False
    # even if we are not going to return all_fields, we need to dictize all the
    # groups so that we can sort by any field.
    group_list = model_dictize.group_list_dictize(
        groups, context,
        sort_key=lambda x: x[sort_info[0][0]],
        reverse=sort_info[0][1] == 'desc',
        with_package_counts=all_fields or
        sort_info[0][0] in ('packages', 'package_count'),
        include_groups=asbool(data_dict.get('include_groups', False)),
        include_tags=include_tags,
        include_extras=include_extras,
        )

    if not all_fields:
        group_list = [group[ref_group_by] for group in group_list]

    return group_list
    
def logic_action_update_package_update(context, data_dict):
    '''Update a dataset (package).

    You must be authorized to edit the dataset and the groups that it belongs
    to.

    It is recommended to call
    :py:func:`ckan.logic.action.get.package_show`, make the desired changes to
    the result, and then call ``package_update()`` with it.

    Plugins may change the parameters of this function depending on the value
    of the dataset's ``type`` attribute, see the
    :py:class:`~ckan.plugins.interfaces.IDatasetForm` plugin interface.

    For further parameters see
    :py:func:`~ckan.logic.action.create.package_create`.

    :param id: the name or id of the dataset to update
    :type id: string

    :returns: the updated dataset (if ``'return_package_dict'`` is ``True`` in
              the context, which is the default. Otherwise returns just the
              dataset id)
    :rtype: dictionary

    '''
    import ckan.lib.plugins as lib_plugins
    import datetime
    import ckan.lib.dictization.model_save as model_save
    import ckan.plugins as plugins
    import ckan.lib.uploader as uploader
    _check_access = ckan.logic.check_access

    model = context['model']
    user = context['user']
    name_or_id = data_dict.get("id") or data_dict['name']

    pkg = model.Package.get(name_or_id)
    if pkg is None:
        raise NotFound(_('Package was not found.'))
    context["package"] = pkg
    data_dict["id"] = pkg.id
    data_dict['type'] = pkg.type

    upload = uploader.Upload('package', '')
    upload.update_data_dict(data_dict, 'image_url', 'image_upload', 'clear_upload')

    _check_access('package_update', context, data_dict)

    # get the schema
    package_plugin = lib_plugins.lookup_package_plugin(pkg.type)
    if 'schema' in context:
        schema = context.pop('schema')
    else:
        schema = package_plugin.update_package_schema()

    if 'api_version' not in context:
        # check_data_dict() is deprecated. If the package_plugin has a
        # check_data_dict() we'll call it, if it doesn't have the method we'll
        # do nothing.
        check_data_dict = getattr(package_plugin, 'check_data_dict', None)
        if check_data_dict:
            try:
                package_plugin.check_data_dict(data_dict, schema)
            except TypeError:
                # Old plugins do not support passing the schema so we need
                # to ensure they still work.
                package_plugin.check_data_dict(data_dict)

    data, errors = lib_plugins.plugin_validate(
        package_plugin, context, data_dict, schema, 'package_update')
    log.debug('package_update validate_errs=%r user=%s package=%s data=%r',
              errors, context.get('user'),
              context.get('package').name if context.get('package') else '',
              data)

    if errors:
        model.Session.rollback()
        raise ckan.logic.ValidationError(errors)

    rev = model.repo.new_revision()
    rev.author = user
    if 'message' in context:
        rev.message = context['message']
    else:
        rev.message = _(u'REST API: Update object %s') % data.get("name")

    #avoid revisioning by updating directly
    model.Session.query(model.Package).filter_by(id=pkg.id).update(
        {"metadata_modified": datetime.datetime.utcnow()})
    model.Session.refresh(pkg)

    upload.upload(uploader.get_max_image_size())
    generateThumbs(upload.filepath)
    pkg = model_save.package_dict_save(data, context)

    context_org_update = context.copy()
    context_org_update['ignore_auth'] = True
    context_org_update['defer_commit'] = True
    ckan.logic.get_action('package_owner_org_update')(context_org_update,
                                            {'id': pkg.id,
                                             'organization_id': pkg.owner_org})

    # Needed to let extensions know the new resources ids
    model.Session.flush()
    if data.get('resources'):
        for index, resource in enumerate(data['resources']):
            resource['id'] = pkg.resources[index].id

    for item in plugins.PluginImplementations(plugins.IPackageController):
        item.edit(pkg)

        item.after_update(context, data)

    # Create default views for resources if necessary
    if data.get('resources'):
        ckan.logic.get_action('package_create_default_resource_views')(
            {'model': context['model'], 'user': context['user'],
             'ignore_auth': True},
            {'package': data})

    if not context.get('defer_commit'):
        model.repo.commit()

    log.debug('Updated object %s' % pkg.name)

    return_id_only = context.get('return_id_only', False)

    # Make sure that a user provided schema is not used on package_show
    context.pop('schema', None)

    # we could update the dataset so we should still be able to read it.
    context['ignore_auth'] = True
    output = data_dict['id'] if return_id_only \
            else ckan.logic.get_action('package_show')(context, {'id': data_dict['id']})

    return output

def generateThumbs(filepath):
    import os.path
    from PIL import Image, ImageOps

    if os.path.isfile(filepath):
        log.warn('file_exists')
        image = Image.open(filepath)
        sizes = [('1', (600, 400)), ('2', (400, 300)), ('3', (280, 200))]

        for size in sizes:
            thumb = ImageOps.fit(image, size[1], Image.ANTIALIAS)
            thumb.save(filepath + "." + size[0] + ".jpg")

def logic_action_create_package_create(context, data_dict):
    '''Create a new dataset (package).

    You must be authorized to create new datasets. If you specify any groups
    for the new dataset, you must also be authorized to edit these groups.

    Plugins may change the parameters of this function depending on the value
    of the ``type`` parameter, see the
    :py:class:`~ckan.plugins.interfaces.IDatasetForm` plugin interface.

    :param name: the name of the new dataset, must be between 2 and 100
        characters long and contain only lowercase alphanumeric characters,
        ``-`` and ``_``, e.g. ``'warandpeace'``
    :type name: string
    :param title: the title of the dataset (optional, default: same as
        ``name``)
    :type title: string
    :param author: the name of the dataset's author (optional)
    :type author: string
    :param author_email: the email address of the dataset's author (optional)
    :type author_email: string
    :param maintainer: the name of the dataset's maintainer (optional)
    :type maintainer: string
    :param maintainer_email: the email address of the dataset's maintainer
        (optional)
    :type maintainer_email: string
    :param license_id: the id of the dataset's license, see
        :py:func:`~ckan.logic.action.get.license_list` for available values
        (optional)
    :type license_id: license id string
    :param notes: a description of the dataset (optional)
    :type notes: string
    :param url: a URL for the dataset's source (optional)
    :type url: string
    :param version: (optional)
    :type version: string, no longer than 100 characters
    :param state: the current state of the dataset, e.g. ``'active'`` or
        ``'deleted'``, only active datasets show up in search results and
        other lists of datasets, this parameter will be ignored if you are not
        authorized to change the state of the dataset (optional, default:
        ``'active'``)
    :type state: string
    :param type: the type of the dataset (optional),
        :py:class:`~ckan.plugins.interfaces.IDatasetForm` plugins
        associate themselves with different dataset types and provide custom
        dataset handling behaviour for these types
    :type type: string
    :param resources: the dataset's resources, see
        :py:func:`resource_create` for the format of resource dictionaries
        (optional)
    :type resources: list of resource dictionaries
    :param tags: the dataset's tags, see :py:func:`tag_create` for the format
        of tag dictionaries (optional)
    :type tags: list of tag dictionaries
    :param extras: the dataset's extras (optional), extras are arbitrary
        (key: value) metadata items that can be added to datasets, each extra
        dictionary should have keys ``'key'`` (a string), ``'value'`` (a
        string)
    :type extras: list of dataset extra dictionaries
    :param relationships_as_object: see :py:func:`package_relationship_create`
        for the format of relationship dictionaries (optional)
    :type relationships_as_object: list of relationship dictionaries
    :param relationships_as_subject: see :py:func:`package_relationship_create`
        for the format of relationship dictionaries (optional)
    :type relationships_as_subject: list of relationship dictionaries
    :param groups: the groups to which the dataset belongs (optional), each
        group dictionary should have one or more of the following keys which
        identify an existing group:
        ``'id'`` (the id of the group, string), or ``'name'`` (the name of the
        group, string),  to see which groups exist
        call :py:func:`~ckan.logic.action.get.group_list`
    :type groups: list of dictionaries
    :param owner_org: the id of the dataset's owning organization, see
        :py:func:`~ckan.logic.action.get.organization_list` or
        :py:func:`~ckan.logic.action.get.organization_list_for_user` for
        available values (optional)
    :type owner_org: string

    :returns: the newly created dataset (unless 'return_id_only' is set to True
              in the context, in which case just the dataset id will
              be returned)
    :rtype: dictionary

    '''

    import ckan.lib.plugins as lib_plugins
    import datetime
    import ckan.lib.dictization.model_save as model_save
    import ckan.plugins as plugins
    import ckan.lib.uploader as uploader
    _check_access = ckan.logic.check_access
    log.warn('logic_action_create_package_create')
    model = context['model']
    user = context['user']

    if 'type' not in data_dict:
        package_plugin = lib_plugins.lookup_package_plugin()
        try:
            # use first type as default if user didn't provide type
            package_type = package_plugin.package_types()[0]
        except (AttributeError, IndexError):
            package_type = 'dataset'
            # in case a 'dataset' plugin was registered w/o fallback
            package_plugin = lib_plugins.lookup_package_plugin(package_type)
        data_dict['type'] = package_type
    else:
        package_plugin = lib_plugins.lookup_package_plugin(data_dict['type'])

    if 'schema' in context:
        schema = context['schema']
    else:
        schema = package_plugin.create_package_schema()

    upload = uploader.Upload('package', '')
    upload.update_data_dict(data_dict, 'image_url', 'image_upload', 'clear_upload')
    
    _check_access('package_create', context, data_dict)

    if 'api_version' not in context:
        # check_data_dict() is deprecated. If the package_plugin has a
        # check_data_dict() we'll call it, if it doesn't have the method we'll
        # do nothing.
        check_data_dict = getattr(package_plugin, 'check_data_dict', None)
        if check_data_dict:
            try:
                check_data_dict(data_dict, schema)
            except TypeError:
                # Old plugins do not support passing the schema so we need
                # to ensure they still work
                package_plugin.check_data_dict(data_dict)

    data, errors = lib_plugins.plugin_validate(
        package_plugin, context, data_dict, schema, 'package_create')
    log.debug('package_create validate_errs=%r user=%s package=%s data=%r',
              errors, context.get('user'),
              data.get('name'), data_dict)

    if errors:
        model.Session.rollback()
        raise ckan.logic.ValidationError(errors)

    rev = model.repo.new_revision()
    rev.author = user
    if 'message' in context:
        rev.message = context['message']
    else:
        rev.message = _(u'REST API: Create object %s') % data.get("name")

    admins = []
    if user:
        user_obj = model.User.by_name(user.decode('utf8'))
        if user_obj:
            admins = [user_obj]
            data['creator_user_id'] = user_obj.id

    pkg = model_save.package_dict_save(data, context)

    upload.upload(uploader.get_max_image_size())
    generateThumbs(upload.filepath)

    model.setup_default_user_roles(pkg, admins)
    # Needed to let extensions know the package and resources ids
    model.Session.flush()
    data['id'] = pkg.id
    if data.get('resources'):
        for index, resource in enumerate(data['resources']):
            resource['id'] = pkg.resources[index].id

    context_org_update = context.copy()
    context_org_update['ignore_auth'] = True
    context_org_update['defer_commit'] = True
    ckan.logic.get_action('package_owner_org_update')(context_org_update,
                                            {'id': pkg.id,
                                             'organization_id': pkg.owner_org})

    for item in plugins.PluginImplementations(plugins.IPackageController):
        item.create(pkg)

        item.after_create(context, data)

    # Make sure that a user provided schema is not used in create_views
    # and on package_show
    context.pop('schema', None)

    # Create default views for resources if necessary
    if data.get('resources'):
        ckan.logic.get_action('package_create_default_resource_views')(
            {'model': context['model'], 'user': context['user'],
             'ignore_auth': True},
            {'package': data})

    if not context.get('defer_commit'):
        model.repo.commit()

    ## need to let rest api create
    context["package"] = pkg
    ## this is added so that the rest controller can make a new location
    context["id"] = pkg.id
    log.debug('Created object %s' % pkg.name)

    return_id_only = context.get('return_id_only', False)

    output = context['id'] if return_id_only \
        else ckan.logic.get_action('package_show')(context, {'id': context['id']})

    return output

def convert_to_dataset_name(url, context):
    from urlparse import urlparse

    o = urlparse(url)
    output = o.path
    
    pos = output.find('/dataset/')
    if pos != -1:
        output = output[pos+9:]
        
    pos = output.find('/')
    if pos != -1:
        output = output[:pos]
    
    return output