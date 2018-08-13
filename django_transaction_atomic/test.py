
from django.core.management import call_command
from django.db import connections, DEFAULT_DB_ALIAS
from django.test import TransactionTestCase
from django.test import TestCase as BaseTestCase

import _atomic as transaction
from ._atomic import atomic as _atomic


def connections_support_transactions():
    """
    Returns True if all connections support transactions.
    """
    return all(conn.features.supports_transactions
               for conn in connections.all())


if transaction.atomic == _atomic:

    # If we are using our backported atomic decorator, then we must provide a
    # backported TestCase to go with it.

    class TestCase(BaseTestCase):
        """
        """

        @classmethod
        def _databases_names(cls, include_mirrors=True):
            # If the test case has a multi_db=True flag, act on all databases,
            # including mirrors or not. Otherwise, just on the default DB.
            if getattr(cls, 'multi_db', False):
                return [
                    alias for alias in connections
                    if (include_mirrors or not
                        connections[alias].settings_dict['TEST']['MIRROR'])
                ]
            else:
                return [DEFAULT_DB_ALIAS]

        @classmethod
        def _enter_atomics(cls):
            """Helper method to open atomic blocks for multiple databases"""
            atomics = {}
            for db_name in cls._databases_names():
                atomics[db_name] = transaction.atomic(using=db_name)
                atomics[db_name].__enter__()
            return atomics

        @classmethod
        def _rollback_atomics(cls, atomics):
            """Rollback atomic blocks opened through the previous method"""
            for db_name in reversed(cls._databases_names()):
                transaction.set_rollback(True, using=db_name)
                atomics[db_name].__exit__(None, None, None)

        @classmethod
        def setUpClass(cls):
            super(TestCase, cls).setUpClass()
            if not connections_support_transactions():
                return

            cls.cls_atomics = cls._enter_atomics()

            if hasattr(cls, 'fixtures'):
                for db_name in cls._databases_names(include_mirrors=False):
                    try:
                        call_command('loaddata', *cls.fixtures, **{
                            'verbosity': 0,
                            'commit': False,
                            'database': db_name,
                        })
                    except Exception:
                        cls._rollback_atomics(cls.cls_atomics)
                        raise
            try:
                cls.setUpTestData()
            except Exception:
                cls._rollback_atomics(cls.cls_atomics)
                raise

        @classmethod
        def tearDownClass(cls):
            if connections_support_transactions():
                cls._rollback_atomics(cls.cls_atomics)
                for conn in connections.all():
                    conn.close()
            super(TestCase, cls).tearDownClass()

        @classmethod
        def setUpTestData(cls):
            """Load initial data for the TestCase"""
            pass

        def _fixture_setup(self):
            return super(TestCase, self)._fixture_setup()

            assert not getattr(self, 'reset_sequences', False), \
                'reset_sequences cannot be used on TestCase instances'

            self.atomics = self._enter_atomics()

        def _fixture_teardown(self):
            return super(TestCase, self)._fixture_teardown()

            try:
                if hasattr(self, '_should_check_constraints'):
                    for db_name in reversed(self._databases_names()):
                        if ((self._should_check_constraints(
                             connections[db_name]))):
                            connections[db_name].check_constraints()
            finally:
                self._rollback_atomics(self.atomics)


else:

    # Otherwise, the builtin TestCase already handles atomic. We should provide
    # it instead.

    TestCase = BaseTestCase
