SkipNose
========

.. image:: https://badge.fury.io/py/skipnose.png
    :target: http://badge.fury.io/py/skipnose

.. image:: https://travis-ci.org/dealertrack/skipnose.png?branch=master
    :target: https://travis-ci.org/dealertrack/skipnose

.. image:: https://coveralls.io/repos/dealertrack/skipnose/badge.png?branch=master
    :target: https://coveralls.io/r/dealertrack/skipnose?branch=master

Nose plugin which allows to include/exclude directories for testing
by their glob pattern. This allows to selectively filter which
tests are executed.

Using
-----

Plugin adds 3 configuration options to nosetests:

``--with-skipnose``
    Required option to enable ``skipnose`` plugin functionality.
    Alternatively can be provided as an environment variable
    ``NOSE_SKIPNOSE`` (e.g. add this to ``.bashrc`` - ``export NOSE_SKIPNOSE=1``).

``--skipnose-exclude``
    This option specifies using glob pattern any folders which nosetests
    should ignore. This option can also be provided multiple times and
    alternatively can be provided as a ``[,;:]``-delimited
    ``NOSE_SKIPNOSE_EXCLUDE`` environment variable::

        $ nosetests --with-skipnose --skipnose-exclude=foo3 --skipnose-exclude=sub2foo?
        $ # is equivalent to
        $ NOSE_SKIPNOSE_EXCLUDE=foo3,sub2foo? nosetests --with-skipnose

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

``--skipnose-include``
    This option specifies using glob pattern the only folders nosetests
    should run. This option can also be provided multiple times and
    alternatively can be provided as a ``[,;:]``-delimited
    ``NOSE_SKIPNOSE_INCLUDE`` environment variable::

        $ nosetests --with-skipnose --skipnose-include=foo3 --skipnose-include=sub2foo?
        $ # is equivalent to
        $ NOSE_SKIPNOSE_INCLUDE=foo3,sub2foo? nosetests --with-skipnose

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

``--skipnose-debug``
    This option enabled some extra print statements for debugging
    to see which folders skipnose includes or excludes.

Difference
----------

Nose already has some options to include and exclude directories by using
``-i`` or ``-e`` options. The exclude mostly works as in this plugin
however the difference can be observed in include functionality.
Let's consider the following folder tree structure::

    tests/
      foo/
        api/                      <= need only subtree
          subapi/
            ...
      bar/
        api/                      <= need only subtree
          ...

Now lets imagine that we need to run only tests within ``tests/foo/api/`` and
``tests/bar/api/``. To accomplish that, we would try to provide a regex
similar to ``"api"`` however that will not work because while determining
whether to go inside either ``foo`` or ``bar`` directories, nose will not
match the regex pattern hence will not execute required tests. To solve
that, we might provide a more complex regex to account for this such as
``^tests/(foo)|(bar)/api`` however that could be more error-prone since
all paths to the ``api`` paths will need to be accounted for.

``skipnose`` solve this from the first try by just specifying a simple include
pattern ``"api"`` (e.g. ``--skipnose-include=api``) and it will just work.
Internally before rejecting any folder, ``skipnose`` matches all directories
within the folder in question subtree. In order words, before rejecting
``tests/foo``, ``skipnose`` will test it's subtree for the given glob pattern
which will find a match at ``tests/foo/api`` hence ``test/foo`` will not be
rejected. In addition, before rejecting ``tests/foo/api/subapi`` since
``subapi`` would not match the pattern, ``skipnose`` tests any of the parent
folders which will allow the ``subapi`` to be accepted.

Hopefully this behaviour makes including specific folders and their subtree
in the test runner a lot more intuitive and simpler to configure.

Testing
-------

To run the tests you need to install testing requirements first::

    $ pip install -r requirements-dev.txt

Then to run tests, you can use ``nosetests``::

    $ nosetests -sv
