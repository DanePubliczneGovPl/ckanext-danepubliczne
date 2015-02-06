import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.lib.plugins

class DatasetForm(p.SingletonPlugin, tk.DefaultDatasetForm):
    '''
    Modifies fields and appearance of datasets
    '''
    p.implements(p.IDatasetForm)
    p.implements(p.ITemplateHelpers) # Helpers for templates

    def get_helpers(self):
        # TODO prefix helpers with dp_
        return {'categories': self.categories,
                'update_frequencies': self.update_frequencies}
    
    def categories(self):
        try: 
            tags = tk.get_action('tag_list')(
                data_dict={'vocabulary_id': 'categories'})
            
            return tags
        except tk.ObjectNotFound:
            return None

    def update_frequencies(self):
        try: 
            tags = tk.get_action('tag_list')(
                data_dict={'vocabulary_id': 'update_frequencies'})
            
            return tags
        except tk.ObjectNotFound:
            return None

    
    def show_package_schema(self):
        schema = super(DatasetForm, self).show_package_schema()
        
        optional = tk.get_validator('ignore_missing')
        from_extras = tk.get_converter('convert_from_extras')
        from_tags = tk.get_converter('convert_from_tags')
        
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))
        schema.update({
            'category': [from_tags('categories')],
            'update_frequency': [from_tags('update_frequencies')],
            'license_restrictions': [from_extras, optional]
        })
        return schema        
        
    def _modify_package_schema(self, schema):
        to_extras = tk.get_converter('convert_to_extras')
        to_tags = tk.get_converter('convert_to_tags')
        optional = tk.get_validator('ignore_missing')
        
        schema.update({
            'category': [to_tags('categories')], # TODO
            'update_frequency': [to_tags('update_frequencies')],
            'license_restrictions': [optional, to_extras],
        })
        # Add our custom_resource_text metadata field to the schema
#         schema['resources'].update({
#                 'custom_resource_text' : [ tk.get_validator('ignore_missing') ]
#                 })
        
        return schema

    ############################
    # Below not interesting code
    
    def package_types(self):
        return [] # handle all dataset types
    
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

