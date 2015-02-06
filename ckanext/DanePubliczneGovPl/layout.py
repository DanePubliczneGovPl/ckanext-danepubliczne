import ckan.plugins as p
import ckan.plugins.toolkit as tk
import mimetypes

class Layout(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    
    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')  
        tk.add_resource('fanstatic', 'dane_publiczne')
        
        # Specify exotic extensions
        mimetypes.add_type('application/json', '.geojson')

    
    
