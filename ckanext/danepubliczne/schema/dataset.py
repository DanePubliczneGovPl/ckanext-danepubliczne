import re
import copy
import json

from webhelpers.html import literal
import ckan.new_authz as new_authz
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
import ckan.lib.helpers as h
import ckan.model as model
from paste.deploy.converters import asbool
from ckanext.qa.plugin import QAPlugin
from ckan.common import _, g, c, request
from ckan import logic
import collections

import logging
log = logging.getLogger(__name__)
ValidationError = logic.ValidationError

class DatasetForm(p.SingletonPlugin, tk.DefaultDatasetForm):
    '''
    Modifies fields and appearance of datasets
    '''

    UPDATE_FREQUENCIES = [
        "yearly",
        "notApplicable",
        "everyHalfYear",
        "daily",
        "weekly",
        "quarterly",
        "monthly"
    ]

    p.implements(p.ITemplateHelpers)  # Helpers for templates

    def get_helpers(self):
        return {'dp_update_frequencies': DatasetForm.h_update_frequencies,
                'dp_update_frequencies_options': DatasetForm.h_update_frequencies_options,
                'dp_package_has_license_restrictions': self.h_package_has_license_restrictions,
                'dp_openess_info': self.h_openess_info,
                'dp_translate_facet': self.h_translate_facet,
                'dp_vocab_reuse_conditions_captions': self.h_vocab_reuse_conditions_captions}

    @classmethod
    def h_update_frequencies(cls):
        return cls.UPDATE_FREQUENCIES

    @classmethod
    def h_update_frequencies_options(cls):
        return ({'value': freq, 'text': cls.h_translate_facet(freq, 'update_frequency')} for freq in
                cls.h_update_frequencies())

    def h_package_has_license_restrictions(self, dpkg):
        return dpkg.get('license_condition_source', False) or dpkg.get('license_condition_original',
                                                                                          False) \
               or dpkg.get('license_condition_modification', False) or dpkg.get('license_condition_responsibilities',
                                                                                False) or dpkg.get(
            'license_condition_db_or_copyrighted', False)

    @classmethod
    def h_openess_info(cls, score):
        if isinstance(score, str) or isinstance(score, unicode):
            score = int(score)

        qa_captions = [
            _('Missing QA information'),
            _('Unstructured data (e.g. PDF)'),
            _('Structured data but proprietry format (e.g. Excel)'),
            _('Structured data in open format (e.g. CSV)'),
            _('Linkable data - served at URIs (e.g. RDF)'),
            _('Linked data - data URIs and linked to other data (e.g. RDF)'),
        ]

        return qa_captions[max(score, 0)]


    p.implements(p.IConfigurer)

    def update_config(self, config):
        # TODO ckan-dev ckan.new_authz should be overridable by IAuthFunctions as well
        # no need to hack it like this then

        # Allow organizations members to add datasets to all non-org groups (categories in our case)
        import ckan.new_authz

        old_has_user_permission_for_group_or_org = ckan.new_authz.has_user_permission_for_group_or_org

        def new_has_user_permission_for_group_or_org(group_id_or_name, user_name, permission):
            sup = old_has_user_permission_for_group_or_org(group_id_or_name, user_name, permission)
            if sup:
                return True

            # Get group
            if not group_id_or_name:
                return False
            group = model.Group.get(group_id_or_name)
            if not group:
                return False

            is_admin_somewhere = new_authz.has_user_permission_for_some_org(user_name, 'admin')
            can_create_dataset_somewhere = new_authz.has_user_permission_for_some_org(user_name, 'create_dataset')

            # Allow organization admins & editors to add and remove packages from groups (categories)
            if (is_admin_somewhere or can_create_dataset_somewhere) and group.type == 'group':
                return True
            return False

        ckan.new_authz.has_user_permission_for_group_or_org = new_has_user_permission_for_group_or_org


        def _make_menu_item_handling_many_package_types(menu_item, title, **kw):
            # See ckan/lib/helpers.py:545

            _menu_items = config['routes.named_routes']
            if menu_item not in _menu_items:
                raise Exception('menu item `%s` cannot be found' % menu_item)
            item = copy.copy(_menu_items[menu_item])
            item.update(kw)
            active = h._link_active(item)

            if c.controller == 'package' and len(menu_item) > 7:
                # Guess type of package
                if request.path == '/':
                    type = 'dataset'

                else:
                    parts = [x for x in request.path.split('/') if x]
                    if len(parts[0]) == 2:  # is it locale? simple check
                        type = parts[1]
                    else:
                        type = parts[0]

                active = type == menu_item[:-7]  # assuming menu_item == '<type>_search'

            needed = item.pop('needed')
            for need in needed:
                if need not in kw:
                    raise Exception('menu item `%s` need parameter `%s`'
                                    % (menu_item, need))
            link = h._link_to(title, menu_item, suppress_active_class=True, **item)
            if active:
                return literal('<li class="active">') + link + literal('</li>')
            return literal('<li>') + link + literal('</li>')

        h._make_menu_item = _make_menu_item_handling_many_package_types


    p.implements(p.IPackageController, inherit=True)

    def before_index(self, pkg_dict):

        # Resource type is multivalue field
        types = []
        types_upper_case = []
        for tag_string in pkg_dict.get('res_type', []):
            if tag_string:
                t = [tag.strip() for tag in tag_string.split(',')]
                tuc = [ti.upper() for ti in t]
                types += t
                types_upper_case += tuc

        pkg_dict['res_type'] = types

        if( pkg_dict.get('type')=='dataset' ):
            try:
                org_dict = logic.action.get.organization_show({
                    'model': model,
                    'ignore_auth': True,
                    'validate': False,
                    'use_cache': False
                }, {
                    'id': pkg_dict.get('organization'),
                    'include_datasets': False,
                    'include_extras': False,
                    'include_users': False,
                    'include_groups': False,
                    'include_tags': False,
                    'include_followers': False
                })
                pkg_dict['institution_type'] = org_dict.get('institution_type') if org_dict.get('institution_type') else "state"
            except:
                pass

        # Resuse conditions
        from paste.deploy.converters import asbool
        # TODO prefix extras_ - create searchable text in PL/EN
        pkg_dict['license_condition_modification'] = asbool(pkg_dict.get('license_condition_modification'))
        pkg_dict['license_condition_original'] = asbool(pkg_dict.get('license_condition_original'))
        pkg_dict['license_condition_source'] = asbool(pkg_dict.get('license_condition_source'))
        pkg_dict['license_condition_responsibilities'] = bool(
            pkg_dict.get('license_condition_responsibilities', '').strip())
        pkg_dict['license_condition_db_or_copyrighted'] = bool(
            pkg_dict.get('license_condition_db_or_copyrighted', '').strip())

        pkg_dict['has_any_reuse_conditions'] = pkg_dict['license_condition_modification'] \
                                               or pkg_dict['license_condition_original'] or pkg_dict[
                                                   'license_condition_source'] \
                                               or pkg_dict[
                                                   'license_condition_responsibilities'] \
                                               or pkg_dict['license_condition_db_or_copyrighted']

        restrictions = []
        for restr in ['modification', 'original', 'source', 'responsibilities', 'db_or_copyrighted']:
            if pkg_dict['license_condition_' + restr]:
                restrictions.append(restr)

        if not restrictions:
            restrictions = ['none']

        pkg_dict['vocab_reuse_conditions'] = restrictions

        # Update frequency (string instead of text solr type)
        pkg_dict['update_frequency'] = pkg_dict.get('extras_update_frequency')

        pkg_dict['status'] = pkg_dict.get('status')
        pkg_dict['api'] = 'with_api' if ('API' in types_upper_case) else ''
        return pkg_dict

    def after_(self, context, pkg_dict):
        self._create_missing_resource_type_tags(pkg_dict)

    def after_create(self, context, pkg_dict):
        self._create_missing_resource_type_tags(pkg_dict)

    def after_update(self, context, pkg_dict):
        self._create_missing_resource_type_tags(pkg_dict)

    def after_show(self, context, pkg_dict):
        pkg_dict['resources_tracking_summary'] = self.calculate_resources_tracking(pkg_dict['resources'])
        pkg_dict['api'] = self.has_api(pkg_dict['resources'])

    def after_search(self, search_results, search_params):
        for i, sr in enumerate(search_results['results']):
            sr['resources_tracking_summary'] = self.calculate_resources_tracking(sr['resources'])
            sr['api'] = self.has_api(sr['resources'])
            search_results['results'][i] = sr
        return search_results

    def has_api(self, resources):
        try:
            for res in resources:
                types = res['resource_type'].split(',')
                types[:] = [t.upper() for t in types]
                if 'API' in types:
                    return True
        except:
            return False
        return False

    def calculate_resources_tracking(self, resources):
        total = 0
        recent = 0
        try:
            for res in resources:
                total += res['tracking_summary']['total']
                recent += res['tracking_summary']['recent']
        except:
            pass
        return {'total': total, 'recent': recent}

    def _create_missing_resource_type_tags(self, pkg_dict):
        context = {'model': model, 'user': g.site_id}

        existing = set(logic.action.get.tag_list(context, {'vocabulary_id': 'resource_types'}))

        resources = pkg_dict.get('resources', [])
        resource_pos = -1
        errors_count = 0
        errors = [{} for i in range(len(resources))]

        for r in resources:
            used = []
            resource_pos += 1
            used += [el.strip() for el in r.get('resource_type', '').split(',') if el.strip() != '']

            missing = set(used) - existing
            for tag in missing:
                try:
                    logic.action.create.tag_create(context, {
                        'name': tag,
                        'vocabulary_id': 'resource_types'
                    })
                except ValidationError, e:
                    errors[resource_pos]['resource_type'] = errors[resource_pos].get('resource_type', []) + e.error_dict['name']
                    errors_count += 1
                except Exception as e:
                    raise Exception("Internal error while creating tags: {}".format(e))

        if errors_count:
            raise ValidationError({'resources': errors})

    p.implements(p.IFacets, inherit=True)

    def dataset_facets(self, facets_dict, package_type):

        if package_type == 'article':
            return {
                'tags': _('Tags'),
            }
        elif package_type == 'application':
            if( new_authz.is_sysadmin(c.user) ):
                return {
                    'status': _('Status'),
                    'tags': _('Tags'),
                }
            else:
                return {
                    'tags': _('Tags'),
                }

        ordered_facets_dict = collections.OrderedDict()
        ordered_facets_dict['organization'] = _('Organizations')
        ordered_facets_dict['institution_type'] = _('Organization type')
        ordered_facets_dict['groups'] = _('Groups')
        ordered_facets_dict['tags'] = _('Tags')
        ordered_facets_dict['api'] = _('API provided')
        ordered_facets_dict['res_format'] = _('Formats')
        ordered_facets_dict['res_type'] = _('Resource types')
        ordered_facets_dict['update_frequency'] = _('Update frequency')
        ordered_facets_dict['res_extras_openness_score'] = _('Openess Score')
        ordered_facets_dict['has_any_reuse_conditions'] = _('Restrictions on reuse')
        return ordered_facets_dict

    @classmethod
    def h_vocab_reuse_conditions_captions(cls):
        return {
            'none': _('No restrictions'),
            'modification': _('Inform about modifications'),
            'original': _('Publish original copy'),
            'source': _('Inform about source'),
            'timestamp': _('Inform about creation & access time'),
            'responsibilities': _('Provider restricts liability'),
            'db_or_copyrighted': _('Restrictions on databases and copyrighted material')
        }

    @classmethod
    def h_translate_facet(cls, label, facet):
        if facet == 'groups':
            group = model.Group.get(label)

            title_i18n = group.extras['title_i18n']
            if isinstance(title_i18n, basestring):
                title_i18n = json.loads(title_i18n)

            return title_i18n[h.lang()]

        elif facet == 'update_frequency':
            return _(re.sub('[A-Z]', lambda m: ' ' + m.group(0), label).title())

        elif facet == 'vocab_reuse_conditions':
            return cls.h_vocab_reuse_conditions_captions()[label]

        elif facet == 'has_any_reuse_conditions':
            if asbool(label):
                return _('Restrictions set')
            else:
                return _('No restrictions')

        elif facet == 'institution_type':
            return _(label.capitalize() + ' administration')

        return label


    def group_facets(self, facets_dict, group_type, package_type):
        return self.dataset_facets(facets_dict, None)

    def organization_facets(self, facets_dict, organization_type, package_type):
        return self.dataset_facets(facets_dict, None)


    p.implements(p.IDatasetForm)

    def show_package_schema(self):
        schema = super(DatasetForm, self).show_package_schema()

        optional = tk.get_validator('ignore_missing')
        from_extras = tk.get_converter('convert_from_extras')
        checkboxes = [from_extras, optional, tk.get_validator('boolean_validator')]

        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))
        schema.update({
            'category': [category_from_group],
            'update_frequency': [from_extras],
            'api': [from_extras],
            # Reuse conditions specified in http://mojepanstwo.pl/dane/prawo/2007,ustawa-dostepie-informacji-publicznej/tresc
            'license_condition_source': checkboxes,
            'license_condition_original': checkboxes,
            'license_condition_modification': checkboxes,
            'license_condition_responsibilities': [from_extras, optional],
            'license_condition_db_or_copyrighted': [from_extras, optional]
        })
        return schema

    def _modify_package_schema(self, schema):
        to_extras = tk.get_converter('convert_to_extras')
        optional = tk.get_validator('ignore_missing')
        not_empty = tk.get_validator('not_empty')
        checkboxes = [optional, tk.get_validator('boolean_validator'), to_extras]

        # License is fixed to Open (Public Domain)
        def fixed_license(value, context):
            return 'other-pd'

        schema.update({
            'category': [category_exists, category_to_group],
            'update_frequency': [not_empty, update_frequency_vocab, to_extras],
            'api': [optional, to_extras],
            'license_id': [fixed_license, unicode],

            # Reuse conditions specified in http://mojepanstwo.pl/dane/prawo/2007,ustawa-dostepie-informacji-publicznej/tresc
            'license_condition_source': checkboxes,
            'license_condition_original': checkboxes,
            'license_condition_modification': checkboxes,
            'license_condition_responsibilities': [optional, to_extras],
            'license_condition_db_or_copyrighted': [optional, to_extras]
        })

        # Name of the resource and its type is obligatory
        schema['resources'].update({
            'name' : [not_empty, unicode],
            'resource_type': [not_empty, unicode]
        })

        return schema

    def package_types(self):
        return []  # handle all dataset types

    def is_fallback(self):
        # Overrides all 
        return True

    def create_package_schema(self):
        schema = super(DatasetForm, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(DatasetForm, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema


# TODO ckan-dev add converters and validators as IValidator? should converters have their own Interface for extending to allow tk.get_converter?
def category_exists(value, context):
    categories = tk.get_action('group_list')(context, {})

    if not value in categories:
        raise df.Invalid(_("Category '{0}' doesn't exist").format(value))
    return value

def update_frequency_vocab(value, context):
    if not value in DatasetForm.UPDATE_FREQUENCIES:
        raise df.Invalid(_('update_frequency should be set to one of following values: ' + ', '.join(DatasetForm.UPDATE_FREQUENCIES)))

    return value

def category_from_group(key, data, errors, context):
    category = None
    for k in data.keys():
        if k[0] == 'groups':
            if category == None and k[2] == 'name':
                category = data[k]
                # data.pop(k) # won't be shown in groups

    data[('category',)] = category


def category_to_group(key, data, errors, context):
    category = data.pop(('category',))

    data[('groups', 0, 'name')] = category
