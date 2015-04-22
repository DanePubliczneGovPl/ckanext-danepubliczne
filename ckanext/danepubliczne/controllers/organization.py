import ckan.controllers.organization as base_organization
import group


class OrganizationController(group.GroupController, base_organization.OrganizationController):
    pass