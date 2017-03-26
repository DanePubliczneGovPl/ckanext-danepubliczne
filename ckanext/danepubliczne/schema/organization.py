import ckan.lib
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.logic.schema
from ckan.common import _

class OrganizationForm(p.SingletonPlugin, ckan.lib.plugins.DefaultOrganizationForm):
    '''
    Modifies fields and appearance of organizations 
    '''

    PROVIDERS_TYPES = [
        ["state", "State administration"],
        ["local", "Local administration"],
    ]

    p.implements(p.IGroupForm)
    p.implements(p.ITemplateHelpers)  # Helpers for templates

    def get_helpers(self):
        return {'dp_update_types_options': OrganizationForm.h_update_providers_types_options}

    @classmethod
    def h_update_providers_types_options(cls):
        return ({'value': val[0], 'text': cls.h_translate_facet(val[1])} for val in cls.PROVIDERS_TYPES)

    @classmethod
    def h_translate_facet(cls, label):
        return _(label)

    def _form_to_db_schema(self, schema):
        to_extras = tk.get_converter('convert_to_extras')
        optional = tk.get_validator('ignore_missing')
        not_empty = tk.get_validator('not_empty')

        default_validators = [not_empty, to_extras]
        schema.update({
            'institution_type': default_validators,
            'address_city': default_validators,
            'address_postal_code': default_validators,
            'address_street': default_validators,
            'website': default_validators,
            'email': default_validators,
            'tel': default_validators,
            'fax': default_validators,
            'regon': default_validators,
            'epuap': default_validators
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
        not_empty = tk.get_validator('not_empty')

        default_validators = [from_extras, optional]
        schema.update({
            # If i don't put these 'extras' entries in schema
            # dictization_functions.augment_data converts ('extras', '0', 'key') -> string
            # to ('extras', '0', '__extras') -> dict
            # and from_extras is cannot match ('extras', '0', 'key') and does nothing
            'extras': {'value': [], 'key': []},
            'address_city': default_validators,
            'address_postal_code': default_validators,
            'address_street': default_validators,
            'website': default_validators,
            'email': default_validators,
            'tel': default_validators,
            'fax': default_validators,
            'regon': default_validators,
            'epuap': default_validators,
            'institution_type': default_validators
        })
        return schema

    ###################################
    # Below not really interesting code

    def new_template(self):
        return 'organization/new.html'

    def about_template(self):
        return 'group/about.html'

    def admins_template(self):
        return 'group/admins.html'

    def bulk_process_template(self):
        return 'group/bulk_process.html'

    # don't override history_template - use group template for history

    def edit_template(self):
        return 'organization/edit.html'

    def activity_template(self):
        return 'group/activity_stream.html'

    def is_fallback(self):
        # Overrides all 
        return False

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