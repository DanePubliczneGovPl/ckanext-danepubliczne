from pylons import config

import json
import ckan.lib.navl.dictization_functions
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.app_globals as app_globals
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import ckan.new_authz as new_authz
from ckan.common import _, c, g, request, response

abort = base.abort
render = base.render
_validate = ckan.lib.navl.dictization_functions.validate

check_access = logic.check_access
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError

import ckan.controllers.user as base_user

class UserController(base_user.UserController):

    def edit(self, id=None, data=None, errors=None, error_summary=None):
        context = {'save': 'save' in request.params,
                   'schema': self._edit_form_to_db_schema(),
                   'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj
                   }
        if id is None:
            if c.userobj:
                id = c.userobj.id
            else:
                abort(400, _('No user specified'))
        data_dict = {'id': id}

        try:
            check_access('user_update', context, data_dict)
        except NotAuthorized:
            abort(401, _('Unauthorized to edit a user.'))

        # Custom handling if user in organization
        action_ctx = context.copy()
        action_ctx['user'] = id
        c.in_organization = bool(logic.get_action('organization_list_for_user')(action_ctx, {}))

        to_json = convert_to_json('about')
        not_empty = tk.get_validator('not_empty')
        context['schema'].update({
            'official_position': [not_empty, to_json],
            'official_phone': [not_empty, to_json]
        })

        # End of custom handling

        if (context['save']) and not data:
            return self._save_edit(id, context)

        try:
            old_data = get_action('user_show')(context, data_dict)

            schema = self._db_to_edit_form_schema()
            if schema:
                old_data, errors = _validate(old_data, schema, context)

            c.display_name = old_data.get('display_name')
            c.user_name = old_data.get('name')

            data = data or old_data

        except NotAuthorized:
            abort(401, _('Unauthorized to edit user %s') % '')
        except NotFound:
            abort(404, _('User not found'))

        user_obj = context.get('user_obj')

        if not (new_authz.is_sysadmin(c.user)
                or c.user == user_obj.name):
            abort(401, _('User %s not authorized to edit %s') %
                  (str(c.user), id))

        errors = errors or {}
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}

        self._setup_template_variables({'model': model,
                                        'session': model.Session,
                                        'user': c.user or c.author},
                                       data_dict)

        c.is_myself = True
        c.show_email_notifications = h.asbool(
            config.get('ckan.activity_streams_email_notifications'))
        c.form = render(self.edit_user_form, extra_vars=vars)

        return render('user/edit.html')


    def _db_to_edit_form_schema(self):
        schema = logic.schema.default_user_schema()

        from_json = convert_from_json('about')
        ignore_missing = tk.get_validator('ignore_missing')
        schema.update({
            'official_position': [from_json, ignore_missing],
            'official_phone': [from_json, ignore_missing],
            'about': []
        })

        return schema


def convert_to_json(field):
    def f(key, data, errors, context):
        j = data.get((field,), {})

        if j:
            j = json.loads(j)

        j[key[0]] = data.pop(key)

        data[(field,)] = json.dumps(j)
    return f

def convert_from_json(field):
    def f(key, data, errors, context):
        j = data.get((field,), {})

        if j:
            j = json.loads(j)
            if key[0] in j:
                data[key] = j[key[0]]

    return f