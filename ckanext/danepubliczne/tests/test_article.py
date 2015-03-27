"""Tests for dp_article"""

import paste.fixture
import pylons.test
import pylons.config as config
import webtest

import nose.tools

assert_equals = nose.tools.assert_equals
assert_raises = nose.tools.assert_raises

import ckan.model as model
import ckan.tests as tests
import ckan.logic as logic
import ckan.plugins
import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers

import ckan.logic.auth.create as auth_create


def _make_article(apikey = None):
    article = {
        'title': u'Article title',
        'name': 'article_name',
        'notes': 'Content',
        'type': 'article'
    }

    if apikey:
        article['apikey'] = apikey

    return article


plugins_to_load = [
    'dane_publiczne_articles',
    'dane_publiczne_dataset',
    'dane_publiczne_organization',
    'dane_publiczne_categories',
    'dane_publiczne'
]


class TestAuth(helpers.FunctionalTestBase):
    @classmethod
    def setup_class(cls):
        super(TestAuth, cls).setup_class()

        ckan.plugins.load(*plugins_to_load)

    # @classmethod
    # def teardown_class(cls):
    #     super(TestAuth, cls).teardown_class()
    #
    #     ckan.plugins.unload(*plugins_to_load)

    # Old style tests becacuse otherwise one cannot test implementing IAuthFunctions
    def test_auth_sysadmin_can_create_article(self):
        sysadmin = factories.Sysadmin()
        article = _make_article(apikey=sysadmin['apikey'])
        app = helpers._get_test_app()

        tests.call_action_api(TestAuth._test_app, 'package_create', **article)

    def test_auth_user_cannot_create_article(self):
        user = factories.User()
        article = _make_article(apikey=user['apikey'])

        # app = helpers._get_test_app()
        app = paste.fixture.TestApp(pylons.test.pylonsapp)
        ckan.plugins.load(*plugins_to_load)

        tests.call_action_api(app, 'package_create', status=403, **article)

    def test_auth_organization_user_cannot_create_article(self):
        user = factories.User()
        org = factories.Organization(users=[
            {
                'name': user['name'],
                'capacity': 'admin'
            }])
        article = _make_article(apikey=user['apikey'])

        # TODO reply that IAuthFunction cannot be tested that way response = auth_create.package_create({'user': None, 'model': model}, article)
        # assert_equals(response['success'], True)

        # TODO This way doesn't work as well, doesn't load plugins :/
        tests.call_action_api(TestAuth._test_app, 'package_create', status=403, **article)

    def test_auth_visitor_cannot_create_article(self):
        article = _make_article()
        app = helpers._get_test_app()

        tests.call_action_api(app, 'package_create', status=403, **article)


class TestAction(helpers.FunctionalTestBase):
    @classmethod
    def setup_class(cls):
        super(TestAction, cls).setup_class()

        ckan.plugins.load(*plugins_to_load)

    @classmethod
    def teardown_class(cls):
        super(TestAction, cls).teardown_class()

        ckan.plugins.unload(*plugins_to_load)

    def _test_required_field(self, field):
        article = _make_article()

        article.pop(field)

        assert_raises(
            logic.ValidationError,
            helpers.call_action,
            'package_create',
            **article
        )

    def test_required_title(self):
        self._test_required_field('title')

    def test_required_notes(self):
        self._test_required_field('notes')

    def test_required_name(self):
        self._test_required_field('name')
