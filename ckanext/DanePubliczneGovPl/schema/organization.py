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
                       'project_leader':default_validators
                       })
        return schema

    def db_to_form_schema(self):
        #schema = super(OrganizationForm, self).form_to_db_schema()
        schema = ckan.logic.schema.default_show_group_schema()
        # should be called by ckan.lib.plugins.DefaultGroupForm.db_to_form_schema
        # or return {}
        #schema = super(OrganizationForm, self).db_to_form_schema()
          
        from_extras = tk.get_converter('convert_from_extras')
        optional = tk.get_validator('ignore_missing')
  
        default_validators = [from_extras, optional]
        schema.update({
                       # If i don't put these 'extras' entries in schema 
                       #  dictization_functions.augment_data converts ('extras', '0', 'key') -> string
                       #  to ('extras', '0', '__extras') -> dict
                       #  and from_extras is cannot match ('extras', '0', 'key') and does nothing
                       'extras': { 'value': [], 'key': []}, 
                       'project_leader':default_validators
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