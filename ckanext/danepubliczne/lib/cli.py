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
        import ckan.model as model

        cmd = self.args[0] if self.args else None
        if cmd == 'required':
            self.required()
        #elif cmd == 'sample':
        #    self.sample()
        else:
            print 'Command %s not recognized' % cmd

    def required(self):
        import ckan.model as model

        vocab = tk.get_action('vocabulary_create')(data_dict={'name': 'resource_types'})
        print 'Added vocabulary resource_types'
