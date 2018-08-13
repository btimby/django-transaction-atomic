try:
    from django import VERSION as django_version

except ImportError:
    from django import __version__ as django_version
    django_version = list(map(int, django_version.split('.')[:2]))

from django.db import connection
from django.test import TestCase, TransactionTestCase

from unittest import skipIf

try:
    from unittest import mock

except ImportError:
    import mock

from . import atomic, commit, rollback, get_connection
from .test import connections_support_transactions
from .models import Model1


def _supports_atomic():
    """Return True if Django version requires patching."""
    return django_version[:2] >= (1, 6)


def _function():
    """
    A function for testing.
    """
    assert connection.in_atomic_block, 'Attribute should be True'


@skipIf(not _supports_atomic(), 'Atomic support is not built in')
class DefaultTestCase(TransactionTestCase):
    """
    Test Case for Django with built-in atomic.
    """

    def test_import(self):
        """Test that patching was NOT done."""
        # Import "real" implementation.
        from django.db.transaction import atomic as _atomic
        from django.db.transaction import commit as _commit
        from django.db.transaction import rollback as _rollback

        # Ensure the originals are used.
        self.assertEqual(atomic, _atomic)
        self.assertEqual(commit, _commit)
        self.assertEqual(rollback, _rollback)


@skipIf(_supports_atomic(), 'Atomic support is built in')
class BackportTestCase(TestCase):
    """
    Test Case for Django lacking atomic.
    """

    def test_decorator(self):
        """Test atomic used as wrapper."""
        wrapped = atomic(_function)
        wrapped()

    def test_nested_fun(self):
        """Test nested atomic usage as wrapper and decorator."""
        wrapped = atomic(_function)

        @atomic
        def nesting():
            return wrapped()

        nesting()

    def test_nested_ctx(self):
        """Test atomic used as context manager."""
        wrapped = atomic(_function)

        with atomic():
            wrapped()


class BleedoverTestCase(TestCase):
    """
    Test Case for test isolation.
    """

    def test_one(self):
        """Ensure objects do not bleed over between tests."""
        self.assertTrue(connections_support_transactions())

        with atomic():
            # First create an object.
            Model1.objects.create(name='1: does it bleed?')

        # Then ensure only that object exists.
        self.assertEqual(1, Model1.objects.all().count())

    def test_two(self):
        """Ensure objects do not bleed over between tests."""
        self.assertTrue(connections_support_transactions())

        with atomic():
            # First create an object.
            Model1.objects.create(name='2: does it bleed?')

        # Then ensure only that object exists.
        self.assertEqual(1, Model1.objects.all().count())


class TransactionBleedoverTestCase(TransactionTestCase):
    """
    Test Case for transaction test isolation.
    """

    def test_one(self):
        """Ensure objects do not bleed over between tests."""
        self.assertTrue(connections_support_transactions())

        with atomic():
            # First create an object.
            Model1.objects.create(name='1: does it bleed?')

        # Then ensure only that object exists.
        self.assertEqual(1, Model1.objects.all().count())

    def test_two(self):
        """Ensure objects do not bleed over between tests."""
        self.assertTrue(connections_support_transactions())

        with atomic():
            # First create an object.
            Model1.objects.create(name='2: does it bleed?')

        # Then ensure only that object exists.
        self.assertEqual(1, Model1.objects.all().count())


class ProxyTestCase(TestCase):
    """
    Test Case for Database / Features Proxies.
    """

    def test_features(self):
        """Test that features is accessible."""
        connection = get_connection()
        self.assertTrue(connection.features.supports_select_related)
