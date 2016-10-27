import logging
import cgi
from urllib import urlencode

from pylons import config
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.jsonp as jsonp
import ckan.lib.maintain as maintain
import ckan.lib.navl.dictization_functions as df
import ckan.lib.helpers as h
import ckan.model as model
import ckan.lib.plugins
import ckan.plugins as p
import ckan.lib.render
import random
import string
from feedback import FeedbackController
from paste.deploy.converters import asbool
from ckan.common import OrderedDict, _, json, request, c, g, response
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.new_authz as new_authz
import ckanext.danepubliczne.plugin as dp
from home import CACHE_PARAMETERS
log = logging.getLogger(__name__)

render = base.render
abort = base.abort
redirect = base.redirect

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key
lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin

def get_action(action):
    if action == 'package_update':
        return dp.logic_action_update_package_update
    elif action == 'package_create':
        return dp.logic_action_create_package_create
    else:
        return logic.get_action(action)

def _encode_params(params):
    return [(k, v.encode('utf-8', 'ignore') if isinstance(v, basestring) else str(v))
            for k, v in params]


def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)


def search_url(params, package_type=None):
    if not package_type or package_type == 'dataset':
        url = h.url_for(controller='package', action='search')
    else:
        url = h.url_for('{0}_search'.format(package_type))
    return url_with_params(url, params)


import ckan.controllers.package as base_package


class PackageController(base_package.PackageController):
    
    def new(self, data=None, errors=None, error_summary=None):
        if data and 'type' in data:
            package_type = data['type']
        else:
            package_type = self._guess_package_type(True)

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params}

        if (package_type == 'application') and (request.method == 'POST') and (request.params.get('from_users') == '1'):
            context['ignore_auth'] = True

        # Package needs to have a organization group in the call to
        # check_access and also to save it
        try:
            check_access('package_create', context)
        except NotAuthorized:
            abort(401, _('Unauthorized to create a package'))

        if context['save'] and not data:
            return self._save_new(context, package_type=package_type)

        data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
            request.params, ignore_keys=CACHE_PARAMETERS))))
        c.resources_json = h.json.dumps(data.get('resources', []))
        # convert tags if not supplied in data
        if data and not data.get('tag_string'):
            data['tag_string'] = ', '.join(
                h.dict_list_reduce(data.get('tags', {}), 'name'))

        errors = errors or {}
        error_summary = error_summary or {}
        # in the phased add dataset we need to know that
        # we have already completed stage 1
        stage = ['active']
        if data.get('state', '').startswith('draft'):
            stage = ['active', 'complete']

        # if we are creating from a group then this allows the group to be
        # set automatically
        data['group_id'] = request.params.get('group') or \
            request.params.get('groups__0__id')

        form_snippet = self._package_form(package_type=package_type)
        form_vars = {'data': data, 'errors': errors,
                     'error_summary': error_summary,
                     'action': 'new', 'stage': stage,
                     'dataset_type': package_type,
                    }
        c.errors_json = h.json.dumps(errors)

        self._setup_template_variables(context, {},
                                       package_type=package_type)

        new_template = self._new_template(package_type)
        c.form = ckan.lib.render.deprecated_lazy_render(
            new_template,
            form_snippet,
            lambda: render(form_snippet, extra_vars=form_vars),
            'use of c.form is deprecated. please see '
            'ckan/templates/package/base_form_page.html for an example '
            'of the new way to include the form snippet'
            )
        #return "done"
        return render(new_template,
                      extra_vars={'form_vars': form_vars,
                                  'form_snippet': form_snippet,
                                  'dataset_type': package_type})
    
    def _save_new(self, context, package_type=None):
        # The staged add dataset used the new functionality when the dataset is
        # partially created so we need to know if we actually are updating or
        # this is a real new.
        is_an_update = False
        ckan_phase = request.params.get('_ckan_phase')
        from ckan.lib.search import SearchIndexError
        try:
            data_dict = clean_dict(dict_fns.unflatten(
                tuplize_dict(parse_params(request.POST))))
            if ckan_phase:
                # prevent clearing of groups etc
                context['allow_partial_update'] = True
                # sort the tags
                if 'tag_string' in data_dict:
                    data_dict['tags'] = self._tag_string_to_list(
                        data_dict['tag_string'])
                if data_dict.get('pkg_name'):
                    is_an_update = True
                    # This is actually an update not a save
                    data_dict['id'] = data_dict['pkg_name']
                    del data_dict['pkg_name']

                    if request.params['save'] == 'finish':
                        data_dict['state'] = 'active'

                        # this is actually an edit not a save
                        pkg_dict = get_action('package_update')(context, data_dict)

                        # redirect to view
                        self._form_save_redirect(pkg_dict['name'], 'new', package_type=package_type)

                    # don't change the dataset state
                    data_dict['state'] = 'draft'
                    # this is actually an edit not a save
                    pkg_dict = get_action('package_update')(context, data_dict)

                    if request.params['save'] == 'go-metadata':
                        # redirect to add metadata
                        url = h.url_for(controller='package',
                                        action='new_metadata',
                                        id=pkg_dict['name'])
                    else:
                        # redirect to add dataset resources
                        url = h.url_for(controller='package',
                                        action='new_resource',
                                        id=pkg_dict['name'])
                    redirect(url)
                # Make sure we don't index this dataset
                if request.params['save'] not in ['go-resource', 'go-metadata', 'finish']:
                    data_dict['state'] = 'draft'
                # allow the state to be changed
                context['allow_state_change'] = True

            data_dict['type'] = package_type
            context['message'] = data_dict.get('log_message', '')

            try:
                if (package_type == 'application') and data_dict['from_users']:
                    context['ignore_auth'] = True
                    data_dict['name'] = 'from_users_' + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(16))
                    data_dict['status'] = 'unverified';
                    data_dict['private'] = 'False';
            except:
                pass

            pkg_dict = get_action('package_create')(context, data_dict)

            if ckan_phase and not request.params['save'] == 'finish':
                # redirect to add dataset resources
                url = h.url_for(controller='package',
                                action='new_resource',
                                id=pkg_dict['name'])
                redirect(url)

            if (package_type == 'application') and data_dict['from_users']:
                h.flash_notice(_('Application has been submitted'))
                redirect('/application')

            self._form_save_redirect(pkg_dict['name'], 'new', package_type=package_type)
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % '')
        except NotFound, e:
            abort(404, _('Dataset not found'))
        except dict_fns.DataError:
            abort(400, _(u'Integrity Error'))
        except SearchIndexError, e:
            try:
                exc_str = unicode(repr(e.args))
            except Exception:  # We don't like bare excepts
                exc_str = unicode(str(e))
            abort(500, _(u'Unable to add package to search index.') + exc_str)
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            if is_an_update:
                # we need to get the state of the dataset to show the stage we
                # are on.
                pkg_dict = get_action('package_show')(context, data_dict)
                data_dict['state'] = pkg_dict['state']
                return self.edit(data_dict['id'], data_dict,
                                 errors, error_summary)
            data_dict['state'] = 'none'
            return self.new(data_dict, errors, error_summary)
    
    def _save_edit(self, name_or_id, context, package_type=None):
        from ckan.lib.search import SearchIndexError
        log.debug('Package save request name: %s POST: %r',
                  name_or_id, request.POST)
        try:
            data_dict = clean_dict(dict_fns.unflatten(
                tuplize_dict(parse_params(request.POST))))
            if '_ckan_phase' in data_dict:
                # we allow partial updates to not destroy existing resources
                context['allow_partial_update'] = True
                if 'tag_string' in data_dict:
                    data_dict['tags'] = self._tag_string_to_list(
                        data_dict['tag_string'])
                del data_dict['_ckan_phase']
                del data_dict['save']
            context['message'] = data_dict.get('log_message', '')
            data_dict['id'] = name_or_id
            pkg = get_action('package_update')(context, data_dict)
            c.pkg = context['package']
            c.pkg_dict = pkg

            self._form_save_redirect(pkg['name'], 'edit', package_type=package_type)
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % id)
        except NotFound, e:
            abort(404, _('Dataset not found'))
        except dict_fns.DataError:
            abort(400, _(u'Integrity Error'))
        except SearchIndexError, e:
            try:
                exc_str = unicode(repr(e.args))
            except Exception:  # We don't like bare excepts
                exc_str = unicode(str(e))
            abort(500, _(u'Unable to update search index.') + exc_str)
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.edit(name_or_id, data_dict, errors, error_summary)
    

    def read(self, id, format='html'):
        if not format == 'html':
            ctype, extension = \
                self._content_type_from_extension(format)
            if not ctype:
                # An unknown format, we'll carry on in case it is a
                # revision specifier and re-constitute the original id
                id = "%s.%s" % (id, format)
                ctype, format = "text/html; charset=utf-8", "html"
        else:
            ctype, format = self._content_type_from_accept()

        response.headers['Content-Type'] = ctype

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}
        data_dict = {'id': id}

        # interpret @<revision_id> or @<date> suffix
        split = id.split('@')
        if len(split) == 2:
            data_dict['id'], revision_ref = split
            if model.is_id(revision_ref):
                context['revision_id'] = revision_ref
            else:
                try:
                    date = h.date_str_to_datetime(revision_ref)
                    context['revision_date'] = date
                except TypeError, e:
                    abort(400, _('Invalid revision format: %r') % e.args)
                except ValueError, e:
                    abort(400, _('Invalid revision format: %r') % e.args)
        elif len(split) > 2:
            abort(400, _('Invalid revision format: %r') %
                  'Too many "@" symbols')

        # check if package exists
        try:
            c.pkg_dict = get_action('package_show')(context, data_dict)
            c.pkg = context['package']
        except NotFound:
            abort(404, _('Dataset not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % id)

        if (c.pkg_dict.get('type') == 'application') and (c.pkg_dict.get('status') == 'unverified') and not new_authz.is_sysadmin(c.user):
            abort(401, _('Unauthorized to read package %s') % id)

        # used by disqus plugin
        c.current_package_id = c.pkg.id
        c.related_count = c.pkg.related_count

        # can the resources be previewed?
        # DROP IT!
        # TODO ckan-dev do we really need to call all these functions (sometimes quite memory demanding) to show labels "Preview' or "More information"
        # If it is needed it needs to be cached!
        # I had memory crashes when dataset contained multiple resources
        for resource in c.pkg_dict['resources']:
            # # Backwards compatibility with preview interface
            # resource['can_be_previewed'] = self._resource_preview(
            #         {'resource': resource, 'package': c.pkg_dict})

            resource_views = get_action('resource_view_list')(
                context, {'id': resource['id']})
            resource['has_views'] = len(resource_views) > 0

        package_type = c.pkg_dict['type'] or 'dataset'
        self._setup_template_variables(context, {'id': id},
                                       package_type=package_type)

        template = self._read_template(package_type)
        template = template[:template.index('.') + 1] + format

        feedback_form = FeedbackController.get_form_items()
        feedback_form += [
            {'name': 'source_type', 'control': 'hidden'},
            {'name': 'source_id', 'control': 'hidden'},
        ]

        if (c.pkg_dict.get('type') == 'application') and c.pkg_dict.get('dataset_name'):
            try:
                data_dict = {
                    'q': '*:*',
                    'fq': '+type:dataset +name:("' + '" OR "'.join(c.pkg_dict.get('dataset_name')) + '")',
                    'facet': 'false',
                    'sort': 'metadata_modified desc',
                }
                query = logic.get_action('package_search')(context, data_dict)
                c.datasets = query['results']
            except:
                pass

        if (c.pkg_dict.get('type') == 'dataset'):
            try:
              data_dict = {
                'q': '*:*',
                'facet': 'false',
                'rows': 3,
                'start': 0,
                'sort': 'metadata_created desc',
                'fq': 'capacity:"public" +type:application +status:verified +dataset_name:' + c.pkg_dict.get('name')
              }
              query = logic.get_action('package_search')(context, data_dict)
              c.apps = query['results']
            except:
                pass

        try:
            return render(template,
                          extra_vars={'dataset_type': package_type, 'feedback_form_items': feedback_form})
        except ckan.lib.render.TemplateNotFound:
            msg = _("Viewing {package_type} datasets in {format} format is "
                    "not supported (template file {file} not found).".format(
                package_type=package_type, format=format, file=template))
            abort(404, msg)

        assert False, "We should never get here"

    def resource_read(self, id, resource_id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}

        try:
            c.package = get_action('package_show')(context, {'id': id})
        except NotFound:
            abort(404, _('Dataset not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read dataset %s') % id)

        for resource in c.package.get('resources', []):
            if resource['id'] == resource_id:
                c.resource = resource
                break
        if not c.resource:
            abort(404, _('Resource not found'))

        # required for nav menu
        c.pkg = context['package']
        c.pkg_dict = c.package
        dataset_type = c.pkg.type or 'dataset'

        # get package license info
        license_id = c.package.get('license_id')
        try:
            c.package['isopen'] = model.Package.\
                get_license_register()[license_id].isopen()
        except KeyError:
            c.package['isopen'] = False

        # TODO: find a nicer way of doing this
        c.datastore_api = '%s/api/action' % config.get('ckan.site_url', '').rstrip('/')

        c.related_count = c.pkg.related_count

        c.resource['can_be_previewed'] = self._resource_preview(
            {'resource': c.resource, 'package': c.package})

        resource_views = get_action('resource_view_list')(
            context, {'id': resource_id})

        # filter out recline views if not in dataproxy
        if not c.resource.get('datastore_active', False):
            resource_views = [view for view in resource_views if not view['view_type'] == 'recline_view']

        c.resource['has_views'] = len(resource_views) > 0

        current_resource_view = None
        view_id = request.GET.get('view_id')
        if c.resource['can_be_previewed'] and not view_id:
            current_resource_view = None
        elif c.resource['has_views']:
            if view_id:
                current_resource_view = [rv for rv in resource_views
                                         if rv['id'] == view_id]
                if len(current_resource_view) == 1:
                    current_resource_view = current_resource_view[0]
                else:
                    abort(404, _('Resource view not found'))
            else:
                current_resource_view = resource_views[0]

        vars = {'resource_views': resource_views,
                'current_resource_view': current_resource_view,
                'dataset_type': dataset_type}

        template = self._resource_template(dataset_type)
        return render(template, extra_vars=vars)

    def _resource_preview(self, data_dict):
        '''Deprecated in 2.3, we don't use it functions so get rid of it'''
        return False

    def _resource_tag_string_to_list(self, tag_string):
        ''' This is used to change tags from a sting to a list of dicts '''
        out = []
        for tag in tag_string.split(','):
            tag = tag.strip()
            if tag:
                out.append({'name': tag,
                            'vocabulary_id': 'resource_tags',
                            'state': 'active'})
        return out

    def search(self):
        from ckan.lib.search import SearchError

        package_type = self._guess_package_type()

        try:
            context = {'model': model, 'user': c.user or c.author,
                       'auth_user_obj': c.userobj}
            check_access('site_read', context)
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))
        
        # unicode format (decoded from utf8)
        q = c.q = request.params.get('q', u'')
        c.query_error = False
        page = self._get_page_number(request.params)

        limit = g.datasets_per_page

        # most search operations should reset the page counter:
        params_nopage = [(k, v) for k, v in request.params.items()
                         if k != 'page']

        def drill_down_url(alternative_url=None, **by):
            return h.add_url_param(alternative_url=alternative_url,
                                   controller='package', action='search',
                                   new_params=by)

        c.drill_down_url = drill_down_url

        def remove_field(key, value=None, replace=None):
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller='package', action='search')

        c.remove_field = remove_field
        if package_type == 'dataset':
            default_sort_by = 'metadata_modified desc' if g.tracking_enabled else None
        else:
            default_sort_by = 'metadata_created desc'
        sort_by = request.params.get('sort', default_sort_by)
        params_nosort = [(k, v) for k, v in params_nopage if k != 'sort']

        def _sort_by(fields):
            """
            Sort by the given list of fields.

            Each entry in the list is a 2-tuple: (fieldname, sort_order)

            eg - [('metadata_modified', 'desc'), ('name', 'asc')]

            If fields is empty, then the default ordering is used.
            """
            params = params_nosort[:]

            if fields:
                sort_string = ', '.join('%s %s' % f for f in fields)
                params.append(('sort', sort_string))
            return search_url(params, package_type)

        c.sort_by = _sort_by
        if sort_by is None:
            c.sort_by_fields = []
        else:
            c.sort_by_fields = [field.split()[0]
                                for field in sort_by.split(',')]

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params, package_type)

        c.search_url_params = urlencode(_encode_params(params_nopage))
        api_search_url_params = None

        try:
            c.fields = []
            # c.fields_grouped will contain a dict of params containing
            # a list of values eg {'tags':['tag1', 'tag2']}
            c.fields_grouped = {}
            search_extras = {}
            fq = '' 
            fq_list = [] # filter statements that will be sent in separate "fq" params (because we want to be able to exclude them selectively from facets) 
            for (param, value) in request.params.items():
                if param not in ['q', 'page', 'sort'] \
                        and len(value) and not param.startswith('_'):
                    if not param.startswith('ext_'):
                        c.fields.append((param, value))
                        fq_list.append('{!tag=%s}%s:"%s"' % (param, param, value))
                        if param not in c.fields_grouped:
                            c.fields_grouped[param] = [value]
                        else:
                            c.fields_grouped[param].append(value)
                    else:
                        search_extras[param] = value

            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'for_view': True,
                       'auth_user_obj': c.userobj}

            if package_type and package_type != 'dataset':
                # Only show datasets of this particular type
                fq += ' +dataset_type:{type}'.format(type=package_type)

                if (package_type == 'application') and not (new_authz.is_sysadmin(c.user)):
                    fq += ' +status:verified'

            else:
                # Unless changed via config options, don't show non standard
                # dataset types on the default search page
                if not asbool(config.get('ckan.search.show_all_types', 'False')):
                    fq += ' +dataset_type:dataset'

            facets = OrderedDict()

            default_facet_titles = {
                'organization': _('Organizations'),
                'groups': _('Groups'),
                'tags': _('Tags'),
                'res_format': _('Formats'),
                'license_id': _('Licenses'),
            }

            for facet in g.facets:
                if facet in default_facet_titles:
                    facets[facet] = default_facet_titles[facet]
                else:
                    facets[facet] = facet

            # Facet titles
            for plugin in p.PluginImplementations(p.IFacets):
                facets = plugin.dataset_facets(facets, package_type)

            c.facet_titles = facets

            facets_keys = []
            for f in facets:
                facets_keys.append("{!ex=" + f + "}" + f)

            data_dict = {
                'q': q,
                'fq': fq.strip(),
                'fq_list': fq_list,
                'facet.field': facets_keys,
                'rows': limit,
                'start': (page - 1) * limit,
                'sort': sort_by,
                'extras': search_extras
            }

            ##### EXTENDING ORIGINAL <<<<<<<<<<
            # API Params
            api_url_params = {
                'q': q,
                'fq': fq.strip(),
                'rows': limit,
                'start': (page - 1) * limit,
            }
            if sort_by:
                api_url_params['sort'] = sort_by
            if facets.keys():
                api_url_params['facet.field'] = json.dumps(facets.keys())
            # if search_extras:
            # api_url_params['extras'] = ','.join(search_extras)

            api_search_url_params = urlencode(_encode_params(api_url_params.items()))
            ##### EXTENDING ORIGINAL >>>>>>>>>>>>>>

            query = get_action('package_search')(context, data_dict)
            c.sort_by_selected = query['sort']

            c.page = h.Page(
                collection=query['results'],
                page=page,
                url=pager_url,
                item_count=query['count'],
                items_per_page=limit
            )
            c.facets = query['facets']
            c.search_facets = query['search_facets']
            c.page.items = query['results']
        except SearchError, se:
            log.error('Dataset search error: %r', se.args)
            c.query_error = True
            c.facets = {}
            c.search_facets = {}
            c.page = h.Page(collection=[])
        c.search_facets_limits = {}
        for facet in c.search_facets.keys():
            try:
                limit = int(request.params.get('_%s_limit' % facet,
                                               g.facets_default_number))
            except ValueError:
                abort(400, _('Parameter "{parameter_name}" is not '
                             'an integer').format(
                    parameter_name='_%s_limit' % facet
                ))
            c.search_facets_limits[facet] = limit

        maintain.deprecate_context_item(
            'facets',
            'Use `c.search_facets` instead.')

        self._setup_template_variables(context, {},
                                       package_type=package_type)

        return render(self._search_template(package_type),
                      extra_vars={'dataset_type': package_type, 'api_search_url_params': api_search_url_params})

    def download(self):
        #from django.http import HttpResponse
        #try:
        from ckan.common import response
        import unicodecsv as csv

        response.headers["Content-Disposition"] = "attachment; filename=resources.csv"
        context = {'model': model, 'session': model.Session, 'user': c.user or c.author, 'auth_user_obj': c.userobj}
        data_dict = {
            'q': '*:*',
            'facet': 'false',
            'start': 0,
            'sort': 'metadata_created desc',
            'fq': 'capacity:"public" +type:dataset'
        }
        query = logic.get_action('package_search')(context, data_dict)
        datasets = query['results']

        writer = csv.writer(response)
        writer.writerow([
        _('ID').encode('utf-8', 'ignore'), 
        _('Name').encode('utf-8', 'ignore'), 
        _('Description').encode('utf-8', 'ignore'), 
        _('URL').encode('utf-8', 'ignore'), 
        _('Format').encode('utf-8', 'ignore'),
        _('Type').encode('utf-8', 'ignore'),
        _('5 Stars of Openness').encode('utf-8', 'ignore'),
        _('Creation Date').encode('utf-8', 'ignore'),
        _('Last Modified').encode('utf-8', 'ignore'),
        _('Dataset name').encode('utf-8', 'ignore'),
        _('Dataset title').encode('utf-8', 'ignore'),
        _('Dataset notes').encode('utf-8', 'ignore'),
        _('Dataset category').encode('utf-8', 'ignore'),
        _('Dataset creation date').encode('utf-8', 'ignore'),
        _('Dataset modification date').encode('utf-8', 'ignore'),
        _('Organization name').encode('utf-8', 'ignore'),
        _('Organization title').encode('utf-8', 'ignore')
        ])
        for dataset in datasets:
            org = dataset.get('organization')
            for resource in dataset.get('resources'):
                writer.writerow([
                resource.get('id'), 
                resource.get('name').encode('utf-8', 'ignore'), 
                resource.get('description').encode('utf-8', 'ignore'), 
                resource.get('url'), 
                resource.get('format'),
                resource.get('resource_type'),
                resource.get('openness_score'),
                resource.get('created'),
                resource.get('last_modified'),
                dataset.get('name').encode('utf-8', 'ignore'), 
                dataset.get('title').encode('utf-8', 'ignore'), 
                dataset.get('notes').encode('utf-8', 'ignore'), 
                dataset.get('category').encode('utf-8', 'ignore'), 
                dataset.get('metadata_created'),
                dataset.get('metadata_modified'),
                org.get('name').encode('utf-8', 'ignore'),
                org.get('title').encode('utf-8', 'ignore'),
                ])
        return response

        #except:
        #    return 'except'
        #    pass

    @jsonp.jsonpify
    def jupload_resource(self, id):
        if not request.method == 'POST':
            abort(400, _('Only POST is supported'))

        data = clean_dict(df.unflatten(tuplize_dict(parse_params(
            request.POST))))

        package_name = data.get('name')
        file = data.get('file')

        if package_name == None or file == None:
            abort(400, _('Missing dataset name or file.'))

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}

        try:
            package_dict = get_action('package_show')(context, {'id': package_name})
        except NotAuthorized:
            abort(401, _('Unauthorized to update dataset'))
        except NotFound:
            abort(404,
              _('The dataset {id} could not be found.').format(id=package_name))

        resource_dict = {
            'package_id': package_name,
            'upload': file,
            'name': file.filename
        }
        try:
            resource = get_action('resource_create')(context, resource_dict)
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.new_resource(id, data, errors, error_summary)
        except NotAuthorized:
            abort(401, _('Unauthorized to create a resource'))
        except NotFound:
            abort(404,
                _('The dataset {id} could not be found.').format(id=id))


        return {"files": [
            {
                "name": file.filename,
                "url": resource['url'],
            }
        ]}
        
    def new_resource(self, id, data=None, errors=None, error_summary=None):
    
        context = {'model': model, 'session': model.Session, 'user': c.user or c.author, 'auth_user_obj': c.userobj}
        pkg_dict = get_action('package_show')(context, {'id': id})

        if pkg_dict.get('type') == 'application':
          redirect('/application/' + id)
        elif pkg_dict.get('type') == 'article':
          redirect('/article/' + id)
        else:
          return super(PackageController, self).new_resource(id, data, errors, error_summary)