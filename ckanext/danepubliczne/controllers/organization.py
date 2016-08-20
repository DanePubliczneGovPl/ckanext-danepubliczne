import ckan.controllers.organization as base_organization
import group
import ckan.model as model
from ckan.common import c, request
import ckan.lib.helpers as h
import ckan.lib.base as base

render = base.render

class OrganizationController(group.GroupController, base_organization.OrganizationController):
    default_sort_by = 'metadata_modified desc'
    
    def index(self):
        group_type = self._guess_group_type()

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'with_private': False}

        q = c.q = request.params.get('q', '')
        org_type = c.type = request.params.get('type', '')
        data_dict = {'all_fields': True, 'q': q}
        sort_by = c.sort_by_selected = request.params.get('sort')
        if sort_by:
            data_dict['sort'] = sort_by
        else:
            data_dict['sort'] = 'title asc' # Sort by title by default

        try:
            self._check_access('site_read', context)
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        # pass user info to context as needed to view private datasets of
        # orgs correctly
        if c.userobj:
            context['user_id'] = c.userobj.id
            context['user_is_admin'] = c.userobj.sysadmin

        if org_type:
            data_dict['extra_conditions'] = [
	            ['institution_type', '==', org_type]
            ]

        results = self._action('group_list')(context, data_dict)

        c.page = h.Page(
            collection=results,
            page = self._get_page_number(request.params),
            url=h.pager_url,
            items_per_page=1
        )
        return render(self._index_template(group_type))