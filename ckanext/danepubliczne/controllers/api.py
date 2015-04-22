import ckan.lib.jsonp as jsonp
import ckan.lib.base as base
import ckan.model as model
import ckan.logic as logic

from ckan.common import c, request


class UtilExtension(base.BaseController):
    @jsonp.jsonpify
    def user_autocomplete_email(self):
        q = request.params.get('q', '')
        limit = request.params.get('limit', 20)
        user_list = []
        if q:
            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'auth_user_obj': c.userobj}

            data_dict = {'q': q, 'limit': limit}

            user_list = logic.get_action('user_autocomplete_email')(context, data_dict)
        return user_list