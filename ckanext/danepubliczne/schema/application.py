import re
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.logic.auth as auth
from ckan.common import _
import ckanext.danepubliczne.plugin as dp

class Application(p.SingletonPlugin, tk.DefaultDatasetForm):
    '''
    Dataset type handling applications
    '''
    p.implements(p.ITemplateHelpers)  # Helpers for templates

    _PACKAGE_TYPE = 'application'

    def get_helpers(self):
        return {
            'dp_recent_application': self.h_recent_applications,
            'dp_shorten_application': self.h_shorten_applications
        }

    def h_recent_applications(self, count=4):
        search = tk.get_action('package_search')(data_dict={
            'rows': count,
            'sort': 'metadata_created desc',
            'fq': '+type:' + Application._PACKAGE_TYPE,
            'facet': 'false'
        })

        if search['count'] == 0:
            return []

        return search['results']

    def h_shorten_applications(self, markdown, length=140, trail='...'):
        # Try to return first paragraph (two consecutive \n disregarding white characters)
        paragraph = markdown
        m = re.search('([ \t\r\f\v]*\n){2}', markdown)
        if m:
            paragraph = paragraph[0:m.regs[0][0]]

        if len(paragraph) > length:
            paragraph = paragraph[0:(length - len(trail))] + trail

        return paragraph


    p.implements(p.IDatasetForm)

    def package_types(self):
        return [Application._PACKAGE_TYPE]

    def is_fallback(self):
        return False

    def _modify_package_schema(self, schema):
        to_extras = tk.get_converter('convert_to_extras')
        to_tags = tk.get_converter('convert_to_tags')
        to_dataset_name = dp.convert_to_dataset_name
        optional = tk.get_validator('ignore_missing')
        boolean_validator = tk.get_validator('boolean_validator')
        not_empty = tk.get_validator('not_empty')
        checkboxes = [optional, tk.get_validator('boolean_validator'), to_extras]

        def fixed_type(value, context):
            return Application._PACKAGE_TYPE

        schema = {
            'id': schema['id'],
            'name': schema['name'],
            'title': [not_empty, unicode],
            'author': schema['author'],
            'notes': [not_empty, unicode],  # notes [content] is obligatory
            'type': [fixed_type],
            'private': [optional, boolean_validator],
            'status': [to_extras],
            'dataset_name': [optional, to_dataset_name, to_extras],
            'tag_string': schema['tag_string'],
            'resources': schema['resources'],
            'image_url': [optional, to_extras],
            'date': [optional, to_extras],
            'app_url': [optional, to_extras]
        }

        return schema

    def show_package_schema(self):
        not_empty = tk.get_validator('not_empty')
        from_extras = tk.get_converter('convert_from_extras')
        from_dataset_name = dp.convert_from_dataset_name

        schema = super(Application, self).show_package_schema()
        schema.update({
            'status': [from_extras],
            'dataset_name': [from_extras, from_dataset_name],
            'image_url': [from_extras],
            'date': [from_extras],
            'app_url': [from_extras],
            'notes': [not_empty, unicode]  # notes [content] is obligatory
        })
        return schema

    def create_package_schema(self):
        schema = super(Application, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(Application, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def new_template(self):
        return 'application/new.html'

    def read_template(self):
        return 'application/read.html'

    def edit_template(self):
        return 'application/edit.html'

    def search_template(self):
        return 'application/search.html'

    #
    # def history_template(self):
    # return 'application/history.html'
    #
    def package_form(self):
        return 'application/new_package_form.html'

    def after_show(self, context, pkg_dict):
        pkg_dict['resources_tracking_summary'] = self.calculate_resources_tracking(pkg_dict['resources'])

    def after_search(self, search_results, search_params):
        for i, sr in enumerate(search_results['results']):
            sr['resources_tracking_summary'] = self.calculate_resources_tracking(sr['resources'])
            search_results['results'][i] = sr
        return search_results