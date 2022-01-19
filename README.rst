==========
ShowFlakes
==========

ShowFlakes is a `pytest <https://docs.pytest.org/en/stable/>`_  plugin to help identify flaky tests.

Installing
==========

ShowFlakes can be installed using ``pip install PATH`` where ``PATH`` is the path to the directory containing ``setup.py``.

Usage
=====

ShowFlakes offers the following command line options:

- ``--record-file=FILENAME`` record test case outcomes to ``FILENAME``. If not given, outcomes are not recorded.
- ``--shuffle`` shuffle the test run order.
- ``--set-exitstatus`` causes the `pytest <https://docs.pytest.org/en/stable/>`_ process to exit with status 0 even if tests failed and 1 if there were any errors.

Output
======

If ``--record-file`` is not set, no output is generated. Otherwise, the output is a tab-separated-values file containing a row for each executed test case. The first column is the test case's outcome (passed, skipped, or failed) and the second is the test case's node ID.