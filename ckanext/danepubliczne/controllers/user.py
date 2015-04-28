import re
import json

from pylons import config
import ckan.lib.navl.dictization_functions as df
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.model as model
import ckan.logic.schema as schema
import ckan.plugins.toolkit as tk
import ckan.lib.captcha as captcha
import ckan.logic as logic
import ckan.lib.mailer as mailer
import ckan.new_authz as new_authz
from ckan.common import _, c, request, response


abort = base.abort
render = base.render

check_access = logic.check_access
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError

import ckan.controllers.user as base_user


class UserController(base_user.UserController):
    def logged_in(self):
        # redirect if needed
        came_from = request.params.get('came_from', '')

        if c.user:
            context = None
            data_dict = {'id': c.user}

            user_dict = get_action('user_show')(context, data_dict)

            user_ref = c.userobj.get_reference_preferred_for_uri()

            if h.url_is_local(came_from) and came_from != '/':
                return h.redirect_to(str(came_from))

            h.redirect_to(locale=None, controller='user', action='dashboard_datasets',
                          id=user_ref)
        else:
            err = _('Login failed. Wrong email or password.')
            if h.asbool(config.get('ckan.legacy_templates', 'false')):
                h.flash_error(err)
                h.redirect_to(controller='user',
                              action='login', came_from=came_from)
            else:
                return self.login(error=err)

    def logged_out(self):
        # came_from = request.params.get('came_from', '')
        # if h.url_is_local(came_from):
        # return h.redirect_to(str(came_from))

        h.redirect_to('/')


    def _unique_email_user_schema(self, schema):
        schema.update({
            'email': schema['email'] + [email_unique_validator]
        })
        return schema

    def _new_form_to_db_schema(self):
        return self._unique_email_user_schema(schema.user_new_form_schema())

    def _edit_form_to_db_schema(self):
        return self._unique_email_user_schema(schema.user_edit_form_schema())

    def _db_to_edit_form_schema(self):
        schema = self._unique_email_user_schema(logic.schema.default_user_schema())

        from_json = convert_from_json('about')
        ignore_missing = tk.get_validator('ignore_missing')
        schema.update({
            'official_position': [from_json, ignore_missing],
            'official_phone': [from_json, ignore_missing],
            'about': []
        })

        return schema

    def _save_new(self, context):
        try:
            data_dict = logic.clean_dict(df.unflatten(
                logic.tuplize_dict(logic.parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')
            captcha.check_recaptcha(request)

            # Extra: Create username from email
            email = data_dict.get('email', '').lower()
            email_user = email.split('@')[0]
            name = re.sub('[^a-z0-9_\-]', '_', email_user)

            # Append num so it becames unique (search inside deleted as well)
            session = context['session']
            user_names = model.User.search(name, session.query(model.User)).all()
            user_names = map(lambda u: u.name, user_names)
            while name in user_names:
                m = re.match('^(.*?)(\d+)$', name)
                if m:
                    name = m.group(1) + str(int(m.group(2)) + 1)
                else:
                    name = name + '2'

            data_dict['name'] = name
            user = get_action('user_create')(context, data_dict)
        except NotAuthorized:
            abort(401, _('Unauthorized to create user %s') % '')
        except NotFound, e:
            abort(404, _('User not found'))
        except df.DataError:
            abort(400, _(u'Integrity Error'))
        except captcha.CaptchaError:
            error_msg = _(u'Bad Captcha. Please try again.')
            h.flash_error(error_msg)
            return self.new(data_dict)
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.new(data_dict, errors, error_summary)
        if not c.user:
            # log the user in programatically
            rememberer = request.environ['repoze.who.plugins']['friendlyform']
            identity = {'repoze.who.userid': data_dict['name']}
            response.headerlist += rememberer.remember(request.environ,
                                                       identity)
            h.redirect_to(controller='user', action='me', __ckan_no_root=True)
        else:
            # #1799 User has managed to register whilst logged in - warn user
            # they are not re-logged in as new user.
            h.flash_success(_('User "%s" is now registered but you are still '
                              'logged in as "%s" from before') %
                            (data_dict['name'], c.user))
            return render('user/logout_first.html')


    def dashboard_search_history(self):
        context = {'for_view': True, 'user': c.user or c.author,
                   'auth_user_obj': c.userobj}
        data_dict = {'user_obj': c.userobj}
        self._setup_template_variables(context, data_dict)

        search_history = get_action('search_history_list')(context, {})

        c.search_history = self._search_history_for_display(search_history)

        return render('user/dashboard_search_history.html')

    def _search_history_for_display(self, search_history):
        for item in search_history:
            facets = item['params']['facet.field']

            q = item['params']['q']
            fq = item['params']['fq']
            facets_set = {}
            for m in re.finditer('\\+?(?P<facet>\\w+)\:(?P<value>(?P<quote>[\'"])(.*?)(?P=quote)|\\w+)', fq[0]):
                facet = m.group('facet')
                value = m.group('value').strip("\"'")
                if facet in facets:
                    facets_set[facet] = value

            url_params = facets_set.copy()
            if q:
                url_params.update({'q': q})

            item['display'] = {
                'q': q,
                'url': h.url_for('search', **url_params),
                'facets': facets_set
            }

        return search_history

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
        c.in_organization = bool(logic.get_action('organization_list_for_user')(action_ctx, {'permission': 'create_dataset'}))

        to_json = convert_to_json('about')
        not_empty = tk.get_validator('not_empty')
        if c.in_organization:
            context['schema'].update({
                'fullname': [not_empty, unicode],
                'official_position': [not_empty, to_json],
                'official_phone': [not_empty, to_json]
            })

        # End of custom handling

        if (context['save']) and not data:
            return self._save_edit(id, context)

        try:
            if not data:
                data = get_action('user_show')(context, data_dict)

                schema = self._db_to_edit_form_schema()
                if schema:
                    data, errors = df.validate(data, schema, context)

                c.display_name = data.get('display_name')
                c.user_name = data.get('name')

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

    def _save_edit(self, id, context):
        try:
            data_dict = logic.clean_dict(df.unflatten(
                logic.tuplize_dict(logic.parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')
            data_dict['id'] = id

            # MOAN: Do I really have to do this here?
            if 'activity_streams_email_notifications' not in data_dict:
                data_dict['activity_streams_email_notifications'] = False

            user = get_action('user_update')(context, data_dict)
            h.flash_success(_('Profile updated'))
            h.redirect_to('user_datasets', id=user['name'])
        except NotAuthorized:
            abort(401, _('Unauthorized to edit user %s') % id)
        except NotFound, e:
            abort(404, _('User not found'))
        except df.DataError:
            abort(400, _(u'Integrity Error'))
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.edit(id, data_dict, errors, error_summary)

    def request_reset(self):
        context = {'model': model, 'session': model.Session, 'user': c.user,
                   'auth_user_obj': c.userobj}

        try:
            check_access('request_reset', context)
        except NotAuthorized:
            abort(401, _('Unauthorized to request reset password.'))

        error = None
        if request.method == 'POST':
            email = request.params.get('email').lower()
            users = model.User.by_email(email)

            if not users:
                error = _('Email not registered: %s') % email

            else:
                try:
                    mailer.send_reset_link(users[0])
                    h.flash_success(_('Please check your inbox for '
                                      'a reset code.'))
                    h.redirect_to('/')
                except mailer.MailerException, e:
                    h.flash_error(_('Could not send reset link: %s') %
                                  unicode(e))

        return render('user/request_reset.html', extra_vars={'error': error})

    def read(self, id=None):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {'id': id,
                     'user_obj': c.userobj,
                     'include_datasets': True,
                     'include_num_followers': True}

        context['with_related'] = True

        self._setup_template_variables(context, data_dict)

        # The legacy templates have the user's activity stream on the user
        # profile page, new templates do not.
        if h.asbool(config.get('ckan.legacy_templates', False)):
            c.user_activity_stream = get_action('user_activity_list_html')(
                context, {'id': c.user_dict['id']})

        return render('user/dashboard_account.html', extra_vars={'userd': c.user_dict})

    def _setup_template_variables(self, context, data_dict):
        super(UserController, self)._setup_template_variables(context, data_dict)

        about = c.user_dict['about']
        if about:
            of = json.loads(about)
            c.user_dict.update(of)


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


def email_unique_validator(key, data, errors, context):
    '''Validates a new email

    Append an error message to ``errors[key]`` if a user with email ``data[key]``
    already exists. Otherwise, do nothing.

    :raises ckan.lib.navl.dictization_functions.Invalid: if ``data[key]`` is
        not a string
    :rtype: None

    '''
    model = context['model']
    new_email = data[key].lower()
    data[key] = new_email

    # if not isinstance(new_email, basestring):
    # raise df.Invalid(_('User names must be strings'))

    session = context['session']
    user = session.query(model.User).filter_by(email=new_email, state='active').first()
    if user:
        # A user with new_email already exists in the database.
        user_obj_from_context = context.get('user_obj')
        if user_obj_from_context and user_obj_from_context.id == user.id:
            # If there's a user_obj in context with the same id as the user
            # found in the db, then we must be doing a user_update and not
            # updating the user name, so don't return an error.
            return
        else:
            # Otherwise return an error: there's already another user with that
            # name, so you can create a new user with that name or update an
            # existing user's name to that name.
            errors[key].append(_('That email is not available.'))
