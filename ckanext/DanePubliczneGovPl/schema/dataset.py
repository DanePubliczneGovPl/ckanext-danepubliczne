import ckan.new_authz as new_authz
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
from ckan.common import _
from ckan import logic

class DatasetForm(p.SingletonPlugin, tk.DefaultDatasetForm):
    '''
    Modifies fields and appearance of datasets
    '''
    p.implements(p.ITemplateHelpers)  # Helpers for templates

    def get_helpers(self):
        return {'dp_update_frequencies': self.update_frequencies,
                'dp_update_frequencies_options': self.update_frequencies_options}

    def update_frequencies(self):
        try:
            tags = tk.get_action('tag_list')(
                data_dict={'vocabulary_id': 'update_frequencies'})

            return tags
        except tk.ObjectNotFound:
            return []

    def update_frequencies_options(self):
        return ({'value': freq, 'text': freq} for freq in self.update_frequencies())


    p.implements(p.IAuthFunctions)
    def get_auth_functions(self):
        return {
            # 'member_create': member_create,
            # 'member_delete': member_delete,
        }



    #
    # p.implements(p.IPackageController, inherit=True)
    # def after_create(self, context, pkg_dict):
    #     group = pkg_dict['category']
    #
    #
    #     r = tk.get_action('member_create')(context, data_dict={
    #         'id': group,
    #         'object': pkg_dict['id'],
    #         'object_type': 'package',
    #         'capacity': 'public'
    #     })
    #


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


def member_create(context, data_dict):
    user = context['user']

    is_admin_somewhere = new_authz.has_user_permission_for_some_org(user, 'admin')

    # Allow organization admins to add and remove packages from groups (categories)
    if is_admin_somewhere and data_dict['object_type'] == 'package' and data_dict['capacity'] == 'public':
        return {'success': True}

    # if not call super
    import ckan.logic.auth.create as ac
    ac.member_create(context, data_dict)

def member_delete(context, data_dict):
    user = context['user']

    is_admin_somewhere = new_authz.has_user_permission_for_some_org(user, 'admin')

    # Allow organization admins to add and remove packages from groups (categories)
    if is_admin_somewhere and data_dict['object_type'] == 'package' and data_dict['capacity'] == 'public':
        return {'success': True}

    # if not call super
    import ckan.logic.auth.create as ad
    ad.member_delete(context, data_dict)