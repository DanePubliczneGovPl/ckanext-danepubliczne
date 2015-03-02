import ckan.lib
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.logic.schema


class OrganizationForm(p.SingletonPlugin, ckan.lib.plugins.DefaultOrganizationForm):
    '''
    Modifies fields and appearance of organizations 
    '''
    p.implements(p.IGroupForm)

    def _form_to_db_schema(self, schema):
        to_extras = tk.get_converter('convert_to_extras')
        optional = tk.get_validator('ignore_missing')

        default_validators = [optional, to_extras]
        schema.update({
            'project_leader': default_validators
        })
        return schema

    # delete in CKAN 2.3
    def _default_show_group_schema(self):
        schema = ckan.logic.schema.default_group_schema()

        # make default show schema behave like when run with no validation
        schema['num_followers'] = []
        schema['created'] = []
        schema['display_name'] = []
        schema['extras'] = {'__extras': [ckan.lib.navl.validators.keep_extras]}
        schema['package_count'] = []
        schema['packages'] = {'__extras': [ckan.lib.navl.validators.keep_extras]}
        schema['revision_id'] = []
        schema['state'] = []
        schema['users'] = {'__extras': [ckan.lib.navl.validators.keep_extras]}

        return schema


    def db_to_form_schema(self):
        # in CKAN 2.3: schema = ckan.logic.schema.default_show_group_schema()
        # TODO should be called by ckan.lib.plugins.DefaultGroupForm.db_to_form_schema
        # or return {}

        # CKAN 2.2
        schema = self._default_show_group_schema()

        from_extras = tk.get_converter('convert_from_extras')
        optional = tk.get_validator('ignore_missing')

        default_validators = [from_extras, optional]
        schema.update({
            # If i don't put these 'extras' entries in schema
            # dictization_functions.augment_data converts ('extras', '0', 'key') -> string
            # to ('extras', '0', '__extras') -> dict
            # and from_extras is cannot match ('extras', '0', 'key') and does nothing
            'extras': {'value': [], 'key': []},
            'project_leader': default_validators
        })
        return schema

    ###################################
    # Below not really interesting code

    def is_fallback(self):
        # Overrides all 
        return True

    def group_types(self):
        return ['organization']

    def form_to_db_schema_api_create(self):
        schema = super(OrganizationForm, self).form_to_db_schema_api_create()
        schema = self._form_to_db_schema(schema)
        return schema

    def form_to_db_schema_api_update(self):
        schema = super(OrganizationForm, self).form_to_db_schema_api_update()
        schema = self._form_to_db_schema(schema)
        return schema

    def form_to_db_schema(self):
        schema = super(OrganizationForm, self).form_to_db_schema()
        schema = self._form_to_db_schema(schema)
        return schema