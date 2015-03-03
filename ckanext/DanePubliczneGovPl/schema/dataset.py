import ckan.plugins as p
import ckan.plugins.toolkit as tk


class DatasetForm(p.SingletonPlugin, tk.DefaultDatasetForm):
    '''
    Modifies fields and appearance of datasets
    '''
    p.implements(p.IDatasetForm)
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

    def show_package_schema(self):
        schema = super(DatasetForm, self).show_package_schema()

        optional = tk.get_validator('ignore_missing')
        from_extras = tk.get_converter('convert_from_extras')
        from_tags = tk.get_converter('convert_from_tags')
        checkboxes = [from_extras, optional, tk.get_validator('boolean_validator')]

        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))
        schema.update({
            'category': [from_tags('categories')],
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
            'category': [to_tags('categories')],
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

    ############################
    # Below not interesting code

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

