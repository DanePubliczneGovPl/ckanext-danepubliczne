import logging
from zope.interface import implements

from repoze.who.interfaces import IAuthenticator
from ckan.model import User


log = logging.getLogger(__name__)


class EmailPasswordAuthenticator(object):
    implements(IAuthenticator)

    def authenticate(self, environ, identity):
        if not ('login' in identity and 'password' in identity):
            return None

        login = identity['login'].lower()
        user_list = User.by_email(login)

        if not user_list:
            log.debug('Login failed - email %r not found', login)
            return None

        user = user_list[0]
        if not user.is_active():
            log.debug('Login as %r failed - user isn\'t active', login)
        elif not user.validate_password(identity['password']):
            log.debug('Login as %r failed - password not valid', login)
        else:
            return user.name

        return None