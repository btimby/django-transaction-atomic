django-transaction-atomic
=========================

Backport of Django `atomic` decorator for older Django versions. This allows
for nesting of transactions in Django 1.4 & 1.5.


Example
-------

.. code:: python

    from django_transaction_atomic import atomic


    @atomic
    def save_something(attr1):
        if attr1 == 3:
            raise Exception()

        return Something.objects.create(attr1=attr1)


    def save_somethings():
        with atomic():
            for i in range(10):
                save_something(i)
        # Entire transaction is rolled back.


Compatability
-------------

+--------------------------------------------------+
| Python                                           |
+====================+=====+=====+=====+=====+=====+
|                    | 2.7 | 3.3 | 3.4 | 3.5 | 3.6 |
+-------------+------+-----+-----+-----+-----+-----+
| Django      | 1.4  |  O  |     |     |     |     |
|             +------+-----+-----+-----+-----+-----+
|             | 1.5  |  O  |  O  |  O  |     |     |
|             +------+-----+-----+-----+-----+-----+
|             | 1.6  |  O  |  O  |  O  |     |     |
|             +------+-----+-----+-----+-----+-----+
|             | 1.7  |  O  |  O  |  O  |     |     |
|             +------+-----+-----+-----+-----+-----+
|             | 1.8  |  O  |  O  |  O  |  O  |  O  |
|             +------+-----+-----+-----+-----+-----+
|             | 1.9  |  O  |     |  O  |  O  |  O  |
|             +------+-----+-----+-----+-----+-----+
|             | 1.10 |  O  |     |  O  |  O  |  O  |
|             +------+-----+-----+-----+-----+-----+
|             | 1.11 |  O  |     |  O  |  O  |  O  |
+-------------+------+-----+-----+-----+-----+-----+
