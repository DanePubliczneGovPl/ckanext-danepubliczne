# -*- coding: UTF-8 -*-
__author__ = 'krzysztofmadejski'

from ckan.lib.cli import CkanCommand
import ckan.plugins.toolkit as tk

class Init(CkanCommand):
    '''Initialize database as required for DanePubliczne

    Usage:
      sysadmin required             - initialize required data
      sysadmin sample               - TODO initialize sample data
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 1
    min_args = 1

    def command(self):
        self._load_config()
        cmd = self.args[0] if self.args else None

        if cmd == 'required':
            self.required()

        elif cmd == 'sample':
            self.create_categories()

        else:
            print 'Command %s not recognized' % cmd

    def required(self):
        try:
            vocab = tk.get_action('vocabulary_create')(data_dict={'name': 'resource_types'})
            print 'Added vocabulary resource_types'
        except Exception, e:
            print e

    def create_categories(self):
        categories = {
            "administracja_publiczna": {
                'title_i18n-pl': u'Administracja Publiczna',
                'title_i18n-en': 'Public Administration',
                'color': '#4b77be',
            },
            "biznes_i_gospodarka": {
                'title_i18n-pl': u'Biznes i Gospodarka',
                'title_i18n-en': 'Business and Economy',
                'color': '#24485f',
            },
            "budzet_i_finanse_publiczne": {
                'title_i18n-pl': u'Budżet i Finanse Publiczne',
                'title_i18n-en': 'Budget and Public Finance',
                'color': '#6c7a89',
            },
            "nauka_i_oswiata": {
                'title_i18n-pl': u'Nauka i Oświata',
                'title_i18n-en': 'Education',
                'color': '#674172',
            },
            "praca_i_pomoc_spoleczna": {
                'title_i18n-pl': u'Praca i Pomoc Społeczna',
                'title_i18n-en': 'Employment and Social Assistance',
                'color': '#bf3607',
            },
            "rolnictwo": {
                'title_i18n-pl': u'Rolnictwo',
                'title_i18n-en': 'Agriculture',
                'color': '#3a539b',
            },
            "spoleczenstwo": {
                'title_i18n-pl': u'Społeczeństwo',
                'title_i18n-en': 'Society',
                'color': '#d35400',
            },
            "sport_i_turystyka": {
                'title_i18n-pl': u'Sport i Turystyka',
                'title_i18n-en': 'Sports and Tourism',
                'color': '#2574a9',
            },
            "srodowisko": {
                'title_i18n-pl': u'Środowisko',
                'title_i18n-en': 'Environment',
                'color': '#138435',
            }
        }

        from pylons import config
        site_url = config['ckan.site_url']

        for cid, data in categories.iteritems():
            g = {
                'name': cid,
                'id': cid,
                'image_url': site_url + '/categories/' + cid.replace('_', '-') + '.png'
            }
            g.update(data)

            tk.get_action('group_create')(data_dict=g)
