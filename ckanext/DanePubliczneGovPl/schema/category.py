import ckan.plugins as p
import ckan.plugins.toolkit as tk

class Category(p.SingletonPlugin):
    '''
    Uses groups as categories of datasets
    '''
    p.implements(p.ITemplateHelpers)

    def get_helpers(self):
        return {'dp_categories': self.categories,
            }

    def categories(self):
        categories = tk.get_action('group_list')(data_dict={'all_fields': True})

        return categories
