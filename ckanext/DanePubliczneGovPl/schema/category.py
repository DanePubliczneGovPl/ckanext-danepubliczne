import ckan.lib
import ckan.plugins as p
import ckan.plugins.toolkit as tk

class Category(p.SingletonPlugin):
    '''
    Uses groups as categories of datasets
    '''
    p.implements(p.ITemplateHelpers)

    def get_helpers(self):
        return {'dp_categories': self.h_categories,
                'dp_category_colors': self.h_colors,
            }

    def h_categories(self):
        categories = tk.get_action('group_list')(data_dict={'all_fields': True})

        return categories

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
