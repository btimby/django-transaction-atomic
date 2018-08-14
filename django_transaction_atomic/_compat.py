# Thin compatability layer for different versions of Django. Allows new Django
# atomic implementation to work without changes.
from __future__ import absolute_import

import types

try:
    from django.utils.decorators import ContextDecorator

except ImportError:
    try:
        from contextlib import ContextDecorator

    except ImportError:
        from contextlib2 import ContextDecorator


try:
    from django.db.utils import Error

except ImportError:
    Error = Exception

try:
    from django.db.utils import ProgrammingError

except ImportError:

    class ProgrammingError(Error):
        pass

from django.core.exceptions import ImproperlyConfigured
from django.db.transaction import TransactionManagementError

try:
    from django.db.backends.sqlite3.base import DatabaseWrapper \
        as SqliteDatabaseWrapper
except ImproperlyConfigured:
    SqliteDatabaseWrapper = None

try:
    from django.db.backends.mysql.base import DatabaseWrapper \
        as MySQLDatabaseWrapper
except ImproperlyConfigured:
    MySQLDatabaseWrapper = None


def setattrdefault(obj, name, value):
    if hasattr(obj, name):
        return
    setattr(obj, name, value)


def patch_is_managed(obj):
    def is_managed(self):
        is_managed = original_is_managed()
        return is_managed or self.in_atomic_block

    try:
        if obj.is_managed == is_managed:
            return

    except AttributeError:
        original_is_managed = lambda: False
    else:
        original_is_managed = obj.is_managed

    obj.is_managed = types.MethodType(is_managed, obj)


class ProxyDatabaseFeatures(object):
    """
    Proxy DatabaseFeatures and augment with properties from later versions of
    Django.
    """

    def __init__(self, features):
        self._features = features

        # TODO: features should depend on the backend, these values are for
        # MySQL.
        setattrdefault(features, 'autocommits_when_autocommit_is_off', False)

    def __getattr__(self, name):
        return getattr(self._features, name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return object.__setattr__(self, name, value)
        return setattr(self._features, name, value)


class ProxyDatabaseWrapper(object):
    """
    Proxy DatabaseWrapper and augment with properties from later versions of
    Django.
    """

    def __init__(self, connection):
        self._connection = connection

        setattrdefault(connection, 'in_atomic_block', False)
        setattrdefault(connection, 'autocommit', True)
        setattrdefault(connection, 'closed_in_transaction', False)
        setattrdefault(connection, 'savepoint_ids', [])
        setattrdefault(connection, 'needs_rollback', False)

        # Proxy features as well.
        setattrdefault(connection, 'features',
                       ProxyDatabaseFeatures(connection.features))

        # And patch some methods.
        patch_is_managed(connection)

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return object.__setattr__(self, name, value)
        return setattr(self._connection, name, value)

    def get_autocommit(self):
        if isinstance(self._connection, SqliteDatabaseWrapper):
            return self._connection.connection.isolation_level in (None, '')

        elif isinstance(self._connection, MySQLDatabaseWrapper):
            sql = "SHOW GLOBAL VARIABLES LIKE 'AUTOCOMMIT'"

            C = self._connection.cursor()
            try:
                C.execute(sql)
                return C.fetchone()[1] in ('ON', '1')

            finally:
                C.close()

        raise NotImplementedError('get_autocommit() not implemented for '
                                  'backend: %s' % self._connection.__class__)

    def set_autocommit(self, autocommit,
                       force_begin_transaction_with_broken_autocommit=False):
        if isinstance(self._connection, SqliteDatabaseWrapper):
            self._connection.connection.isolation_level = \
                None if autocommit else ''

        elif isinstance(self._connection, MySQLDatabaseWrapper):
            sql = 'SET AUTOCOMMIT='
            sql += '1' if autocommit else '0'

            C = self._connection.cursor()
            try:
                C.execute(sql)

            finally:
                C.close()

        else:
            raise NotImplementedError(
                'set_autocommit() not implemented for '
                'backend: %s' % self._connection.__class__)

    def set_rollback(self, rollback):
        if not self.in_atomic_block:
            raise TransactionManagementError(
                "The rollback flag doesn't work outside of an 'atomic' block.")
        self.needs_rollback = rollback
