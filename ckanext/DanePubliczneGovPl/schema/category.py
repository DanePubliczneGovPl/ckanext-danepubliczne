import ckan.lib
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
from ckan.common import _

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

    p.implements(p.IRoutes, inherit=True)
    def before_map(self, map):
        from routes.mapper import SubMapper
        with SubMapper(map, controller='group') as m:
            m.connect('group_index', '/category', action='index',
                      highlight_actions='index search')
            m.connect('group_list', '/category/list', action='list')
            m.connect('group_new', '/category/new', action='new')
            m.connect('group_action', '/category/{action}/{id}',
                      requirements=dict(action='|'.join([
                          'edit',
                          'delete',
                          'member_new',
                          'member_delete',
                          'history',
                          'followers',
                          'follow',
                          'unfollow',
                          'admins',
                          'activity',
                      ])))
            m.connect('group_about', '/category/about/{id}', action='about',
                      ckan_icon='info-sign'),
            m.connect('group_edit', '/category/edit/{id}', action='edit',
                      ckan_icon='edit')
            m.connect('group_members', '/category/members/{id}', action='members',
                      ckan_icon='group'),
            m.connect('group_activity', '/category/activity/{id}/{offset}',
                      action='activity', ckan_icon='time'),
            m.connect('group_read', '/category/{id}', action='read',
                      ckan_icon='sitemap')
            
        return map
        