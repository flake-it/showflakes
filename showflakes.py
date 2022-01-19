import os
import pytest
import random


class ShowFlakes:
    def __init__(self, record_file):
        self.record_file = record_file

        if record_file is not None and os.path.exists(record_file):
            os.remove(record_file)

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, session, config, items):
        if config.getoption("shuffle"):
            random.shuffle(items)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item, nextitem):
        self.outcome = "passed"

        yield
        
        if self.record_file is not None:
            with open(self.record_file, "a") as f:
                f.write(self.outcome + "\t" + item.nodeid + "\n")

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        result = yield
        report = result.get_result()

        if report.skipped:
            self.outcome = "skipped"
        elif report.failed:
            self.outcome = "failed"

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session, exitstatus):
        if session.config.getoption("set-exitstatus"):
            if exitstatus in (0, 1):
                session.exitstatus = 0
            else:
                session.exitstatus = 1


def pytest_addoption(parser):
    group = parser.getgroup("showflakes")
    
    group.addoption(
        "--record-file", action="store", dest="record-file", type=str
    )

    group.addoption(
        "--shuffle", action="store_true", dest="shuffle",
    )

    group.addoption(
        "--set-exitstatus", action="store_true", dest="set-exitstatus",
    )


def pytest_configure(config):
    record_file = config.getoption("record-file")
    config.pluginmanager.register(ShowFlakes(record_file))
