import re
import ckan.new_authz as new_authz
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
import ckan.lib.helpers as h
import ckan.model as model
from ckanext.qa.plugin import QAPlugin
from ckan.common import _, g
from ckan import logic

class DatasetForm(p.SingletonPlugin, tk.DefaultDatasetForm):
    '''
    Modifies fields and appearance of datasets
    '''
    p.implements(p.ITemplateHelpers)  # Helpers for templates

    def get_helpers(self):
        return {'dp_update_frequencies': self.h_update_frequencies,
                'dp_update_frequencies_options': self.h_update_frequencies_options,
                'dp_package_has_license_restrictions': self.h_package_has_license_restrictions,
                'dp_openess_info': self.h_openess_info}

    def h_update_frequencies(self):
        try:
            tags = tk.get_action('tag_list')(
                data_dict={'vocabulary_id': 'update_frequencies'})

            return tags
        except tk.ObjectNotFound:
            return []

    def h_update_frequencies_options(self):
        return ({'value': freq, 'text': _(re.sub('[A-Z]', lambda m: ' ' + m.group(0), freq).title())} for freq in self.h_update_frequencies())

    def h_package_has_license_restrictions(self, dpkg):
        return dpkg.get('license_condition_source', False) or dpkg.get('license_condition_timestamp',False) or dpkg.get('license_condition_original',False) \
            or dpkg.get('license_condition_modification',False) or dpkg.get('license_condition_responsibilities',False)

    @classmethod
    def h_openess_info(cls, score):
        if isinstance(score, str) or isinstance(score, unicode):
            score = int(score)

        qa_captions = [_('Missing QA information')] + QAPlugin.get_qa_captions()

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
            is_editor_somewhere = new_authz.has_user_permission_for_some_org(user_name, 'editor')

            # Allow organization admins & editors to add and remove packages from groups (categories)
            if (is_admin_somewhere or is_editor_somewhere) and group.type == 'group':
                return True
            return False

        ckan.new_authz.has_user_permission_for_group_or_org = new_has_user_permission_for_group_or_org



    p.implements(p.IPackageController, inherit=True)
    def before_index(self, pkg_dict):
        # Resource type is multivalue field
        types = []
        for tag_string in pkg_dict.get('res_type', []):
            if tag_string:
                types += [tag.strip() for tag in tag_string.split(',')]

        pkg_dict['res_type'] = types


        # Resuse conditions
        from paste.deploy.converters import asbool
        # TODO prefix extras_ - create searchable text in PL/EN
        pkg_dict['license_condition_modification'] = asbool(pkg_dict.get('license_condition_modification'))
        pkg_dict['license_condition_original'] = asbool(pkg_dict.get('license_condition_original'))
        pkg_dict['license_condition_source'] = asbool(pkg_dict.get('license_condition_source'))
        pkg_dict['license_condition_timestamp'] = asbool(pkg_dict.get('license_condition_timestamp'))
        pkg_dict['license_condition_responsibilities'] = bool(pkg_dict.get('license_condition_responsibilities','').strip())

        pkg_dict['has_any_reuse_conditions'] = pkg_dict['license_condition_modification'] \
            or pkg_dict['license_condition_original'] or pkg_dict['license_condition_source'] \
            or pkg_dict['license_condition_timestamp'] or pkg_dict['license_condition_responsibilities']

        restrictions = []
        for restr in ['modification', 'original', 'source', 'timestamp', 'responsibilities']:
            if pkg_dict['license_condition_' + restr]:
                restrictions.append(restr)

        if not restrictions:
            restrictions = ['none']

        pkg_dict['vocab_reuse_conditions'] = restrictions


        return pkg_dict

    def after_create(self, context, pkg_dict):
        self._create_missing_resource_type_tags(pkg_dict)

    def after_update(self, context, pkg_dict):
        self._create_missing_resource_type_tags(pkg_dict)

    def _create_missing_resource_type_tags(self, pkg_dict):
        context = {'model': model, 'user': g.site_id}

        existing = logic.action.get.tag_list(context, {'vocabulary_id': 'resource_types'})

        used = []
        for r in pkg_dict.get('resources', []):
            used += [el.strip() for el in r.get('resource_type', '').split(',') if el.strip() != '']

        missing = set(used) - set(existing)
        for tag in missing:
            try:
                logic.action.create.tag_create(context, {
                    'name': tag,
                    'vocabulary_id': 'resource_types'
                })
            except Exception as e:
                raise Exception("Internal error while creating tags")



    p.implements(p.IFacets, inherit=True)
    def dataset_facets(self, facets_dict, package_type):
        if package_type == 'article':
            return {
                'tags': _('Tags'),
            }

        facets_dict.pop('license_id', None)

        facets_dict['res_type'] = _('Resource types')
        facets_dict['res_extras_openness_score'] = _('Openess Score')
        facets_dict['vocab_reuse_conditions'] = _('Restrictions on reuse of this dataset')

        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        return self.dataset_facets(facets_dict, None)

    def organization_facets(self, facets_dict, organization_type, package_type):
        return self.dataset_facets(facets_dict, None)



    p.implements(p.IDatasetForm)
    def show_package_schema(self):
        schema = super(DatasetForm, self).show_package_schema()

        optional = tk.get_validator('ignore_missing')
        from_extras = tk.get_converter('convert_from_extras')
        from_tags = tk.get_converter('convert_from_tags')
        checkboxes = [from_extras, optional, tk.get_validator('boolean_validator')]

        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))
        schema.update({
            'category': [category_from_group],
            'update_frequency': [from_tags('update_frequencies')],

            # Reuse conditions specified in http://mojepanstwo.pl/dane/prawo/2007,ustawa-dostepie-informacji-publicznej/tresc
            'license_condition_source': checkboxes,
            'license_condition_timestamp': checkboxes,
            'license_condition_original': checkboxes,
            'license_condition_modification': checkboxes,
            'license_condition_responsibilities': [from_extras, optional]
        })
        return schema

    def _modify_package_schema(self, schema):
        to_extras = tk.get_converter('convert_to_extras')
        to_tags = tk.get_converter('convert_to_tags')
        optional = tk.get_validator('ignore_missing')
        checkboxes = [optional, tk.get_validator('boolean_validator'), to_extras]

        # License is fixed to Open (Public Domain)
        def fixed_license(value, context):
            return 'other-pd'

        schema.update({
            'category': [category_exists, category_to_group],
            'update_frequency': [to_tags('update_frequencies')],

            'license_id': [fixed_license, unicode],

            # Reuse conditions specified in http://mojepanstwo.pl/dane/prawo/2007,ustawa-dostepie-informacji-publicznej/tresc
            'license_condition_source': checkboxes,
            'license_condition_timestamp': checkboxes,
            'license_condition_original': checkboxes,
            'license_condition_modification': checkboxes,
            'license_condition_responsibilities': [optional, to_extras]
        })
        # Add our custom_resource_text metadata field to the schema
        # schema['resources'].update({
        # 'custom_resource_text' : [ tk.get_validator('ignore_missing') ]
        # })

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
