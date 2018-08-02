# Thin compatability layer for different versions of Django. Allows new Django
# atomic implementation to work without changes.

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


class ProxyDatabaseFeatures(object):
    """
    Proxy DatabaseFeatures and augment with properties from later versions of
    Django.
    """

    def __init__(self, features):
        self._features = features

        # TODO: features should depend on the backend, these values are for
        # MySQL.
        setattr(features, 'autocommits_when_autocommit_is_off', False)

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

        setattr(connection, 'in_atomic_block', False)
        setattr(connection, 'autocommit', False)
        setattr(connection, 'closed_in_transaction', False)
        setattr(connection, 'savepoint_ids', [])

        # Proxy features as well.
        setattr(connection, 'features',
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
