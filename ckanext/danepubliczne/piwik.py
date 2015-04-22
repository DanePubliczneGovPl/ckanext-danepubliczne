# -*- coding: utf-8 -*-


# CKANExt-Etalab -- CKAN extension for Etalab
# By: Emmanuel Raviart <emmanuel@raviart.com>
#
# Copyright (C) 2013 Etalab
# http://github.com/etalab/ckanext-etalab
#
# This file is part of CKANExt-Etalab.
#
# CKANExt-Etalab is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# CKANExt-Etalab is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from biryani import baseconv, custom_conv, states
from ckan import plugins
import ckan.plugins.toolkit as tk


conv = custom_conv(baseconv, states)


class PiwikPlugin(plugins.SingletonPlugin):
    site_id = None
    url = None
    domain = None
    error = None
    cookies_disabled = None

    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)

    def configure(self, config):
        config.update(conv.check(conv.struct({
            'piwik.site_id': conv.input_to_int,
            'piwik.url': conv.make_input_to_url(full=True, error_if_fragment=True, error_if_path=True,
                                                error_if_query=True),
            'piwik.in_debug': conv.pipe(conv.guess_bool, conv.default(False)),
            'piwik.domain': conv.default(False),
            'piwik.cookies_disabled': conv.default(False),
        }, default='drop'))(config, state=conv.default_state))

        self.site_id = config['piwik.site_id']
        self.url = config['piwik.url']
        self.domain = config['piwik.domain']
        self.cookies_disabled = config['piwik.cookies_disabled']

        if config['debug'] and not config.get('piwik.in_debug'):
            self.error = 'Piwik is disabled in DEBUG mode unless PIWIK_IN_DEBUG is set'
        elif not config.get('piwik.url') or not config.get('piwik.site_id'):
            self.error = 'Piwik is missing configuration'

    def get_helpers(self):
        # Tell CKAN what custom template helper functions this plugin provides,
        # see the ITemplateHelpers plugin interface.
        return {'piwik': self.render_piwik}

    def render_piwik(self):
        return tk.render_snippet('snippets/piwik.html', dict(piwik={
            'error': self.error,
            'url': self.url.strip('/'),
            'site_id': self.site_id,
            'domain': self.domain,
            'cookies_disabled': self.cookies_disabled
        }))