import ckan.controllers.organization as base_organization
import group


class OrganizationController(group.GroupController, base_organization.OrganizationController):
    default_sort_by = 'metadata_modified desc'
