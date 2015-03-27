import logging
from urllib import urlencode

import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.model as model
import ckan.lib.plugins
import ckan.lib.render
from feedback import FeedbackController

from ckan.common import OrderedDict, _, json, request, c, g, response

log = logging.getLogger(__name__)

render = base.render
abort = base.abort
redirect = base.redirect

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key

lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
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

        # used by disqus plugin
        c.current_package_id = c.pkg.id
        c.related_count = c.pkg.related_count

        # can the resources be previewed?
        # DROP IT!
        # TODO ckan-dev do we really need to call all these functions (sometimes quite memory demanding) to show labels "Preview' or "More information"
        # If it is needed it needs to be cached!
        # I had memory crashes when dataset contained multiple resources
        for resource in c.pkg_dict['resources']:
        #     # Backwards compatibility with preview interface
        #     resource['can_be_previewed'] = self._resource_preview(
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

        try:
            return render(template,
                          extra_vars={'dataset_type': package_type, 'feedback_form_items': feedback_form})
        except ckan.lib.render.TemplateNotFound:
            msg = _("Viewing {package_type} datasets in {format} format is "
                    "not supported (template file {file} not found).".format(
                    package_type=package_type, format=format, file=template))
            abort(404, msg)

        assert False, "We should never get here"

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