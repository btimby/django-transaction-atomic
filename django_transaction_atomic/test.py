
from django.test import TestCase as BaseTestCase
from django.test import TransactionTestCase


from . import atomic
from ._atomic import atomic as _atomic


if atomic == _atomic:

    # If we are using our backported atomic decorator, then we must provide a
    # backported TestCase to go with it.

    class TestCase(BaseTestCase):
        """
        """

        def _fixture_setup(self):
            return super(TestCase, self)._fixture_setup()


else:

    # Otherwise, the builtin TestCase already handles atomic. We should provide
    # it instead.

    TestCase = BaseTestCase
