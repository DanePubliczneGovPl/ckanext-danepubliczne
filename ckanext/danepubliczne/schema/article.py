import re

import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.logic.auth as auth
from ckan.common import _


class Article(p.SingletonPlugin, tk.DefaultDatasetForm):
    '''
    Dataset type handling articles
    '''
    p.implements(p.ITemplateHelpers)  # Helpers for templates

    _PACKAGE_TYPE = 'article'

    def get_helpers(self):
        return {
            'dp_recent_articles': self.h_recent_articles,
            'dp_shorten_article': self.h_shorten_article
        }

    def h_recent_articles(self, count=4):
        search = tk.get_action('package_search')(data_dict={
            'rows': count,
            'sort': 'metadata_created desc',
            'fq': '+type:' + Article._PACKAGE_TYPE,
            'facet': 'false'
        })

        if search['count'] == 0:
            return []

        return search['results']

    def h_shorten_article(self, markdown, length=140, trail='...'):
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
        return [Article._PACKAGE_TYPE]

    def is_fallback(self):
        return False

    def _modify_package_schema(self, schema):
        to_extras = tk.get_converter('convert_to_extras')
        to_tags = tk.get_converter('convert_to_tags')
        optional = tk.get_validator('ignore_missing')
        boolean_validator = tk.get_validator('boolean_validator')
        not_empty = tk.get_validator('not_empty')
        checkboxes = [optional, tk.get_validator('boolean_validator'), to_extras]

        def fixed_type(value, context):
            return Article._PACKAGE_TYPE

        schema = {
            'id': schema['id'],
            'name': schema['name'],
            'title': [not_empty, unicode],
            'author': schema['author'],
            'notes': [not_empty, unicode],  # notes [content] is obligatory
            'type': [fixed_type],
            'private': [optional, boolean_validator],
            'license_id': [not_empty, unicode],
            'tag_string': schema['tag_string'],
            'resources': schema['resources']
        }

        return schema

    def show_package_schema(self):
        not_empty = tk.get_validator('not_empty')

        schema = super(Article, self).show_package_schema()
        schema.update({
            'notes': [not_empty, unicode],  # notes [content] is obligatory
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

    def search_template(self):
        return 'article/search.html'

    #
    # def history_template(self):
    # return 'article/history.html'
    #
    def package_form(self):
        return 'article/new_package_form.html'


    p.implements(p.IAuthFunctions)

    def get_auth_functions(self):
        return {
            'package_create': _package_create,  # new = context.get('package') == None
            'package_delete': _package_delete,  # data_dict['id]
            'package_update': _package_update,  # context['package'].type
        }


def _package_create(context, data_dict=None):
    user = context['user']
    package = context.get('package')  # None for new

    if package and package['type'] == 'article':
        return {'success': False, 'msg': _('User %s not authorized to create articles') % user}

    return auth.create.package_create(context, data_dict)


def _package_delete(context, data_dict=None):
    user = context['user']
    package = auth.get_package_object(context, data_dict)

    if package and package.type == 'article':
        return {'success': False, 'msg': _('User %s not authorized to delete articles') % user}

    return auth.delete.package_delete(context, data_dict)


def _package_update(context, data_dict=None):
    user = context['user']
    package = auth.get_package_object(context, data_dict)

    if package and package.type == 'article':
        return {'success': False, 'msg': _('User %s not authorized to update articles') % user}

    return auth.update.package_update(context, data_dict)

