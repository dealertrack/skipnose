DtNose
======

DealerTrack Nose plugin which allows to conditionally include
tests in the test runner by the folder they bold in.

To achieve that, the plugin adds 3 configuration options to nosetests:

:``--dtnose``:
    This option enables the ``dtnose`` plugin and should be provided
    if its features need to be used. Alternatively to passing an option
    to nose (e.g. ``nosetests --dtnose``), this can be provided as an
    environment variable ``export NOSE_DTNOSE=1``.
:``--dtnose-exclude``:
    This option specifies using glob pattern any folders which nosetests
    should ignore. This option can also be provided multiple times and
    alternatively can be provided as a ``[,;:]``-delimited
    ``NOSE_DTNOSE_EXCLUDE`` environment variable::

        $ nosetests --dtnose --dtnose-exclude=foo3 --dtnose-exclude=sub2foo?
        $ # is equivalent to
        $ NOSE_DTNOSE_EXCLUDE=foo3,sub2foo? nosetests --dtnose

    which would result in the following folders being excluded in the tests::

        tests/
          foo1/
            sub1foo1/
              ...
            sub2foo1/             <= excluded
              ...
          foo2/
            sub1foo2/
              ...
            sub2foo2/             <= excluded
              ...
          foo3/                   <= excluded
            sub1foo3/             <= excluded
              ...
            sub2foo3/             <= excluded
              ...

:``--dtnose-include``:
    This option specifies using glob pattern the only folders nosetests
    should run. This option can also be provided multiple times and
    alternatively can be provided as a ``[,;:]``-delimited
    ``NOSE_DTNOSE_INCLUDE`` environment variable::

        $ nosetests --dtnose --dtnose-exclude=foo3 --dtnose-include=sub2foo?
        $ # is equivalent to
        $ NOSE_DTNOSE_INCLUDE=foo3,sub2foo? nosetests --dtnose

    which would result in only the following folders being included in the tests::

        tests/
          foo1/
            sub1foo1/
              ...
            sub2foo1/             <= only this will run
              ...
          foo2/
            sub1foo2/
              ...
            sub2foo2/             <= only this will run
              ...
          foo3/                   <= only this will run
            sub1foo3/             <= only this will run
              ...
            sub2foo3/             <= only this will run
              ...
