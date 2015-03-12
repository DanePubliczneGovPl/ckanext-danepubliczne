import ckan.lib
import ckan.logic
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
from ckan.common import _
from __builtin__ import True

class Category(p.SingletonPlugin, ckan.lib.plugins.DefaultGroupForm):
    '''
    Uses groups as categories of datasets
    '''
    p.implements(p.ITemplateHelpers)

    def get_helpers(self):
        return {'dp_categories': self.h_categories,
                'dp_categories_home': self.h_categories_home,
                'dp_category_colors': self.h_colors,
            }

    def h_categories(self):
        categories = tk.get_action('group_list')(data_dict={'all_fields': True})
        
        return categories
    
    def h_categories_home(self):
        categories = tk.get_action('group_list')(data_dict={'all_fields': True, 'include_extras': True})
        
        categories2 = []
        for c in categories:
            if c['package_count'] == 0:
                continue
            
            for extra in c['extras']:
                if extra['key'] == 'color':
                    c['color'] = extra['value']
        
            categories2.append(c)
            
        return categories2

    def h_colors(self):
        return [
            '#4b77be',
            '#24485f',
            '#6c7a89',
            '#674172',
            '#bf3607',
            '#3a539b',
            '#d35400',
            '#2574a9',
            '#138435'
        ]
        
    p.implements(p.IGroupForm)
    def is_fallback(self):
        return False
    
    def group_types(self):
        return ['group']

    def _form_to_db_schema(self, schema):
        to_extras = tk.get_converter('convert_to_extras')
        not_empty = tk.get_validator('not_empty')

        schema.update({
            'color': [not_empty, to_extras]
        })
        return schema

    def db_to_form_schema(self):
        schema = ckan.logic.schema.default_show_group_schema()

        from_extras = tk.get_converter('convert_from_extras')
        optional = tk.get_validator('ignore_missing')        

        default_validators = [from_extras, optional]
        schema.update({
            # If i don't put these 'extras' entries in schema
            # dictization_functions.augment_data converts ('extras', '0', 'key') -> string
            # to ('extras', '0', '__extras') -> dict
            # and from_extras is cannot match ('extras', '0', 'key') and does nothing
            'extras': {'value': [], 'key': []},
            'color': default_validators
        })
        return schema
    
    def form_to_db_schema(self):
        schema = super(Category, self).form_to_db_schema()
        schema = self._form_to_db_schema(schema)
        return schema
    
    form_to_db_schema_api_create = form_to_db_schema_api_update = form_to_db_schema


    