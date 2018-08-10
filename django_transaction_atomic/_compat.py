# Thin compatability layer for different versions of Django. Allows new Django
# atomic implementation to work without changes.
from __future__ import absolute_import

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


from django.db.transaction import TransactionManagementError


def setattrdefault(obj, name, value):
    if hasattr(obj, name):
        return
    setattr(obj, name, value)


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
        setattrdefault(connection, 'autocommit', False)
        setattrdefault(connection, 'closed_in_transaction', False)
        setattrdefault(connection, 'savepoint_ids', [])
        setattrdefault(connection, 'needs_rollback', False)

        # Proxy features as well.
        setattrdefault(connection, 'features',
                       ProxyDatabaseFeatures(connection.features))

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            return object.__setattr__(self, name, value)
        return setattr(self._connection, name, value)

    def get_autocommit(self):
        return self.autocommit

    def set_autocommit(self, autocommit,
                       force_begin_transaction_with_broken_autocommit=False):
        # TODO: actually implement this.
        self.autocommit = True

    def set_rollback(self, rollback):
        if not self.in_atomic_block:
            raise TransactionManagementError(
                "The rollback flag doesn't work outside of an 'atomic' block.")
        self.needs_rollback = rollback