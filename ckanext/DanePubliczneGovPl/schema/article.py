import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.lib.plugins
import ckan.lib.navl.dictization_functions as df

class Article(p.SingletonPlugin, tk.DefaultDatasetForm):
    '''
    Dataset type handling articles
    '''
    p.implements(p.IDatasetForm)
    p.implements(p.ITemplateHelpers) # Helpers for templates

    _PACKAGE_TYPE = 'article'

    def get_helpers(self):
        return {} # TODO

    def package_types(self):
        return [Article._PACKAGE_TYPE]

    def is_fallback(self):
        return False

    def _modify_package_schema(self, schema):
        to_extras = tk.get_converter('convert_to_extras')
        to_tags = tk.get_converter('convert_to_tags')
        optional = tk.get_validator('ignore_missing')
        not_empty = tk.get_validator('not_empty')
        checkboxes = [optional, tk.get_validator('boolean_validator'), to_extras]

        # License is fixed to Creative Commons Share-Alike
        def fixed_license(value, context):
            return 'cc-by-sa'
        def fixed_type(value, context):
            return Article._PACKAGE_TYPE

        schema = {
            'id': schema['id'],
            'name': schema['name'],
            'title': schema['title'],
            'author': schema['author'],
            'notes': [not_empty, unicode], # notes [content] is obligatory
            'type': [fixed_type],
            'license_id': [fixed_license, unicode],
            }

        return schema

    def show_package_schema(self):
        not_empty = tk.get_validator('not_empty')

        schema = super(Article, self).show_package_schema()
        schema.update({
            'notes': [not_empty, unicode], # notes [content] is obligatory
        })
        return schema

    def create_package_schema(self):
        schema = super(Article, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(Article, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def new_template(self):
        return 'article/new.html'

    def read_template(self):
        return 'article/read.html'

    def edit_template(self):
        return 'article/edit.html'
    #
    # def search_template(self):
    #     return 'article/search.html'
    #
    # def history_template(self):
    #     return 'article/history.html'
    #
    def package_form(self):
        return 'article/new_package_form.html'
