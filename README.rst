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

- ``--record-file=FILENAME`` record test case outcomes to ``FILENAME``. If not given, outcomes are not recorded and selection mode is disabled.
- ``--selection-file=FILENAME`` read node IDs of selected test cases from ``FILENAME``. If not given, selection mode is disabled.
- ``--max-runs=N`` perform a maximum of ``N`` reruns of selected test cases in selection mode. Ignored if selection mode is disabled.
- ``--max-fail=N`` tolerate a maximum of ``N`` failed reruns in selection mode. Ignored if selection mode is disabled.
- ``--max-time=N`` allow up to ``N`` seconds of runtime for a single rerun in selection mode. Ignored if selection mode is disabled.
- ``--n-extra=N`` randomly select up to ``N`` other test cases to execute in reruns in selection mode. Ignored if selection mode is disabled.
- ``--shuffle`` shuffle the test run order.
- ``--deprioritize`` set the NICE value of any child processes or threads spawned during test case execution to a random value between its default value and 20. Ignored if selection mode is disabled.
- ``--mock-flaky`` register a fake ``flaky`` marker for test suites that expect the `flaky <https://github.com/box/flaky/>`_  plugin.
- ``--set-exitstatus`` causes the `pytest <https://docs.pytest.org/en/stable/>`_ process to exit with status 0 even if tests failed and 1 if there were any errors. This is default behavior in selection mode.

Selection Mode
--------------

If both ``--record-file`` and ``--selection-file`` are set, selection mode is enabled. With selection mode enabled, only the test cases specified in the selection file are executed (unless ``--n-extra`` is specified). The selection file should be a list of node IDs (one per line). These test cases are then repeatedly executed until either any of them produce an inconsistent outcome (flaky), the maximum number of reruns are exceeded (specified by ``--max-runs``), or the maximum number of failed reruns are exceeded (specified by ``--max-fails``). A rerun is considered failed if the `pytest <https://docs.pytest.org/en/stable/>`_ process returns a non-zero exit status, it exceeds the maximum runtime (specified by ``--max-time``), or if no test cases are executed. If selection mode is disabled, the entire test suite is executed just once as normal.

Output
======

If ``--record-file`` is not set, no output is generated. Otherwise, if selection mode is enabled, the output is a `JSON <https://www.json.org/json-en.html>`_ file. The file maps the node IDs of the selected test cases to a list containing the number of times the test case failed followed by the number of times it was executed. If selection mode is disabled, the output is a tab-separated-values file containing a row for each executed test case. The first column is the test case's outcome (passed, skipped, or failed) and the second is the test case's node ID.