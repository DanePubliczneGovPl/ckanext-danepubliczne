import ckan.lib.base as base
import ckan.controllers.home as base_home

class HomeController(base_home.HomeController):

    def sitemap(self):
        return base.render('home/sitemap.html')
