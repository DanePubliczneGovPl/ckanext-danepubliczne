from pylons import config

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.app_globals as app_globals
import ckan.model as model
import ckan.logic as logic
import ckan.new_authz
from ckan.common import _

import ckan.controllers.admin as base_admin

class AdminController(base_admin.AdminController):
    def _get_config_form_items(self):
        # Styles for use in the form.select() macro.
        styles = [{'text': 'Default', 'value': '/base/css/main.css'},
                  {'text': 'Red', 'value': '/base/css/red.css'},
                  {'text': 'Green', 'value': '/base/css/green.css'},
                  {'text': 'Maroon', 'value': '/base/css/maroon.css'},
                  {'text': 'Fuchsia', 'value': '/base/css/fuchsia.css'}]

        items = [
            {'name': 'ckan.site_title', 'control': 'input', 'label': _('Site Title'), 'placeholder': ''},
            {'name': 'ckan.site_description', 'control': 'input', 'label': _('Site Tag Line'), 'placeholder': ''},
            {'name': 'ckan.site_logo', 'control': 'input', 'label': _('Site Tag Logo'), 'placeholder': ''},
            {'name': 'ckan.site_about', 'control': 'markdown', 'label': _('About'), 'placeholder': _('About page text')},
            {'name': 'ckan.site_intro_text', 'control': 'markdown', 'label': _('Intro Text'), 'placeholder': _('Text on home page')},
            {'name': 'ckanext.danepubliczne.maintenance_flash', 'control': 'input', 'label': _('Maintenance alert'), 'placeholder': _('Fill if there is planned maintenance break')},
        ]
        return items

    # def config(self):
    #
    #     items = self._get_config_form_items()
    #     data = request.POST
    #     if 'save' in data:
    #         # update config from form
    #         for item in items:
    #             name = item['name']
    #             if name in data:
    #                 app_globals.set_global(name, data[name])
    #         app_globals.reset()
    #         h.redirect_to(controller='admin', action='config')
    #
    #     data = {}
    #     for item in items:
    #         name = item['name']
    #         data[name] = config.get(name)
    #
    #     vars = {'data': data, 'errors': {}, 'form_items': items}
    #     return base.render('admin/config.html',
    #                        extra_vars = vars)
    #
