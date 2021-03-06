import os
import sys
import unittest

from django.conf import settings


def configure_settings():
    settings.configure(
        DEBUG=True,
        USE_TZ=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
            }
        },
        CACHES={
            "default": {
                "BACKEND": "gaekit.caches.GAEMemcachedCache"
            }
        },
        DEFAULT_FILE_STORAGE='gaekit.storages.CloudStorage',
        INSTALLED_APPS=[
            "gaekit",
            "tests",
        ],
        SITE_ID=1,
        ROOT_URLCONF='tests.urls',
    )


def configure_wagtail_settings():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.wagtail_settings")


def patch_wagtail_settings():
    # fix fixture paths to be absolute paths
    from wagtail import tests
    from wagtail.wagtailimages.tests import test_models
    fixture_path = os.path.join(
        os.path.dirname(tests.__file__), 'fixtures', 'test.json')
    test_models.TestUsageCount.fixtures = [fixture_path]
    test_models.TestGetUsage.fixtures = [fixture_path]
    test_models.TestGetWillowImage.fixtures = [fixture_path]
    from wagtail.wagtailimages.tests import tests
    tests.TestMissingImage.fixtures = [fixture_path]
    from wagtail.wagtailimages.tests import test_rich_text
    test_rich_text.TestImageEmbedHandler.fixtures = [fixture_path]

    # skip these test - they rely on media URL matching filename
    from wagtail.wagtailimages.tests.tests import TestMissingImage
    TestMissingImage.test_image_tag_with_missing_image = \
        unittest.skip('Unsupported')(
            TestMissingImage.test_image_tag_with_missing_image)
    TestMissingImage.test_rich_text_with_missing_image = \
        unittest.skip('Unsupported')(
            TestMissingImage.test_rich_text_with_missing_image)

    # filter these warnings
    import warnings
    warnings.simplefilter('default', DeprecationWarning)
    warnings.simplefilter('default', PendingDeprecationWarning)


def init_django():
    try:
        import django
        setup = django.setup
    except AttributeError:
        pass
    else:
        setup()


def init_testbed():
    from google.appengine.ext import testbed
    testbed = testbed.Testbed()
    testbed.activate()
    testbed.init_all_stubs()


def run_tests(*test_args):
    settings_func = configure_settings
    tests = ['tests']

    if 'wagtail' in test_args:
        settings_func = configure_wagtail_settings
        tests = ['wagtail.wagtailimages.tests']

    settings_func()
    init_testbed()
    init_django()

    if 'wagtail' in test_args:
        patch_wagtail_settings()

    from django.test.utils import get_runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    failures = test_runner.run_tests(tests)
    sys.exit(bool(failures))

if __name__ == '__main__':
    run_tests(*sys.argv[1:])
