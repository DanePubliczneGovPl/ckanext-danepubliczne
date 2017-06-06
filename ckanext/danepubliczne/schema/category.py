import ckan.lib
import ckan.logic
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as df
from ckan.plugins.toolkit import missing, _, get_validator, Invalid

import json
import re

class Category(p.SingletonPlugin, ckan.lib.plugins.DefaultGroupForm):
    '''
    Uses groups as categories of datasets
    '''
    p.implements(p.ITemplateHelpers)

    def get_helpers(self):
        return {'dp_categories': self.h_categories,
                'dp_category_colors': self.h_colors,
                'dp_default_locale': self.h_default_locale,
                'fluent_form_languages': self.h_fluent_form_languages,
                }

    def h_fluent_form_languages(self, arg1, arg2):
        langs = []
        for l in h.get_available_locales():
            if l.language not in langs:
                langs.append(l.language)
        return langs

    def h_default_locale(self):
        return h.get_available_locales()[0].language

    def h_categories(self, exclude_empty=False):
        categories = tk.get_action('group_list')(data_dict={'all_fields': True, 'include_extras': True})

        categories2 = []
        for c in categories:
            if c['package_count'] == 0 and exclude_empty:
                continue

            for extra in c['extras']:
                if extra['key'] == 'color':
                    c['color'] = extra['value']
                if extra['key'] == 'title_i18n':
                    c['title_i18n'] = unpack_json_or_text(extra['value'])

            categories2.append(c)

            if c.get('title_i18n'):
                c['title'] = c['title_i18n'][h.lang()]
            else:
                c['title'] = c['display_name']

        return categories2

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

    p.implements(p.IGroupForm)

    def is_fallback(self):
        return True

    def group_types(self):
        return ['group']

    def _form_to_db_schema(self, schema):
        to_extras = tk.get_converter('convert_to_extras')
        not_empty = tk.get_validator('not_empty')
        optional = tk.get_validator('ignore_missing')

        schema.update({
            'color': [not_empty, to_extras],
            'title_i18n': [fluent_text, not_empty, to_extras],
            'description': [fluent_text, optional]
        })
        return schema

    def db_to_form_schema(self):
        schema = ckan.logic.schema.default_show_group_schema()

        from_extras = tk.get_converter('convert_from_extras')
        optional = tk.get_validator('ignore_missing')

        default_validators = [from_extras, optional]
        schema.update({
            # If i don't put these 'extras' entries in schema
            # dictization_functions.augment_data converts ('extras', '0', 'key') -> string
            # to ('extras', '0', '__extras') -> dict
            # and from_extras is cannot match ('extras', '0', 'key') and does nothing
            'extras': {'value': [], 'key': []},
            'color': default_validators,
            'title_i18n': [from_extras, optional, unpack_json_or_text],
            'description': [optional, unpack_json_or_text]
        })
        return schema

    def form_to_db_schema(self):
        schema = super(Category, self).form_to_db_schema()
        schema = self._form_to_db_schema(schema)
        return schema

    form_to_db_schema_api_create = form_to_db_schema_api_update = form_to_db_schema


def unpack_json_or_text(value):
    if isinstance(value, basestring):
        try:
            return json.loads(value)
        except Exception:
            return {h.lang(): value}

    return value

# taken from ckanext-fluent
def fluent_text(key, data, errors, context):
    # just in case there was an error before our validator,
    # bail out here because our errors won't be useful
    if errors[key]:
        return

    ISO_639_LANGUAGE = u'^[a-z][a-z][a-z]?[a-z]?$'
    required_langs = [] # Functionality to be used one day

    value = data[key]
    # 1 or 2. dict or JSON encoded string
    if value is not missing:
        if isinstance(value, basestring):
            try:
                value = json.loads(value)
            except ValueError:
                errors[key].append(_('Failed to decode JSON string'))
                return
            except UnicodeDecodeError:
                errors[key].append(_('Invalid encoding for JSON string'))
                return
        if not isinstance(value, dict):
            errors[key].append(_('expecting JSON object'))
            return

        for lang, text in value.iteritems():
            try:
                m = re.match(ISO_639_LANGUAGE, lang)
            except TypeError:
                errors[key].append(_('invalid type for language code: %r')
                    % lang)
                continue
            if not m:
                errors[key].append(_('invalid language code: "%s"') % lang)
                continue
            if not isinstance(text, basestring):
                errors[key].append(_('invalid type for "%s" value') % lang)
                continue
            if isinstance(text, str):
                try:
                    value[lang] = text.decode('utf-8')
                except UnicodeDecodeError:
                    errors[key]. append(_('invalid encoding for "%s" value')
                        % lang)

        for lang in required_langs:
            if value.get(lang):
                continue
            errors[key].append(_('Required language "%s" missing') % lang)

        if not errors[key]:
            data[key] = json.dumps(value)
        return

    # 3. separate fields
    output = {}
    prefix = key[-1] + '-'
    extras = data.get(key[:-1] + ('__extras',), {})

    for name, text in extras.iteritems():
        if not name.startswith(prefix):
            continue
        lang = name.split('-', 1)[1]
        m = re.match(ISO_639_LANGUAGE, lang)
        if not m:
            errors[name] = [_('invalid language code: "%s"') % lang]
            output = None
            continue

        if output is not None:
            output[lang] = text

    for lang in required_langs:
        if extras.get(prefix + lang):
            continue
        errors[key[:-1] + (key[-1] + '-' + lang,)] = [_('Missing value')]
        output = None

    if output is None:
        return

    for lang in output:
        del extras[prefix + lang]
    data[key] = json.dumps(output)