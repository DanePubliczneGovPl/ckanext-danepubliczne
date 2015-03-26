from pylons import config

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.app_globals as app_globals
import ckan.model as model
import ckan.logic as logic
import ckan.new_authz

c = base.c
request = base.request
_ = base._

class FeedbackController(base.BaseController):

    @classmethod
    def get_form_items(cls):
        items = [
            {'name': 'feedback', 'control': 'textarea', 'label': _('Your feedback'), 'placeholder': _('What is your feedback on this dataset?'), 'required':True},
            {'name': 'email', 'control': 'input', 'label': _('Email'), 'placeholder': _('Leave email if we should get back to you')},
        ]
        return items

    def submit(self):
        data = request.POST
        if not data.get('source_type') in ['package', 'resource'] or not data.get('source_id'):
            base.abort(400)

        source_url = h.url_for(data['source_type'] + '_read', id=data['source_id'])

        h.flash_success(_('Thank you for your feedback!'))
        h.redirect_to(source_url)

    def reset_config(self):
        if 'cancel' in request.params:
            h.redirect_to(controller='admin', action='config')

        if request.method == 'POST':
            # remove sys info items
            for item in self._get_config_form_items():
                name = item['name']
                app_globals.delete_global(name)
            # reset to values in config
            app_globals.reset()
            h.redirect_to(controller='admin', action='config')

        return base.render('admin/confirm_reset.html')

    def config(self):

        items = self._get_config_form_items()
        data = request.POST
        if 'save' in data:
            # update config from form
            for item in items:
                name = item['name']
                if name in data:
                    app_globals.set_global(name, data[name])
            app_globals.reset()
            h.redirect_to(controller='admin', action='config')

        data = {}
        for item in items:
            name = item['name']
            data[name] = config.get(name)

        vars = {'data': data, 'errors': {}, 'form_items': items}
        return base.render('admin/config.html',
                           extra_vars = vars)