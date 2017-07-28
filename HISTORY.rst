.. :changelog:

History
-------

0.3.1 (2017-07-28)
~~~~~~~~~~~~~~~~~~

* Using wheels for distribution
* Excluding tests from being installed
* Added importanize as CI step

0.3.0 (2017-02-18)
~~~~~~~~~~~~~~~~~~

* **New** ``--skipnose-include`` clauses now can either be ANDed or ORed.

  ANDed example::

  	 --skipnose-include=foo  --skipnose-include=bar

  ORed example::

  	--skipnose-include=foo:bar

0.2.0 (2016-02-24)
~~~~~~~~~~~~~~~~~~

* **New** added ``--skipnose-skip-tests`` option

0.1.2 (2015-04-29)
~~~~~~~~~~~~~~~~~~

* Fixed installation bug which prevented skipnose being installed
  already installed nose.
  See `#1 <https://github.com/dealertrack/skipnose/pull/1>`_.

0.1.1 (2014-09-02)
~~~~~~~~~~~~~~~~~~

* Restructured project using cookiecutter template
* Python3 and PYPY support

0.1.0 (2014-08-01)
~~~~~~~~~~~~~~~~~~

* Initial release
