import gc
import os
import json
import time
import pytest
import random

from psutil import AccessDenied, NoSuchProcess, Process, TimeoutExpired


def make_selection(selection_file, items):
    nodeids = set()

    with open(selection_file, "r") as fd:
        for line in fd:
            nid = line.strip().split("[", 1)[0]
            nodeids.add(nid)

    selection, remaining = [], []

    for it in items:
        nid = it.nodeid.split("[", 1)[0]

        if nid in nodeids:
            selection.append(it)
        else:
            remaining.append(it)

    return selection, remaining


def deprioritize_tasks(proc, tasks):
    tasks_new = set()

    try:
        threads = proc.threads()
        children = proc.children()
    except NoSuchProcess:
        return

    for tid, _, _ in threads:
        if tid == proc.pid:
            continue
        
        try:
            proc_task = Process(pid=tid)
        except NoSuchProcess:
            continue
            
        tasks_new.add(proc_task)

    for proc_task in children:
        tasks_new.add(proc_task)

    for proc_task in list(tasks):
        if not proc_task.is_running():
            tasks.remove(proc_task)

    for proc_task in tasks_new - tasks:
        try:
            old_nice = proc_task.nice()
            new_nice = random.randint(old_nice, 20)
            proc_task.nice(new_nice)
            tasks.add(proc_task)
        except (AccessDenied, NoSuchProcess):
            continue


class ShowFlakes:
    def __init__(self, record_file):
        self.record_file = record_file
        self.record = None

        if record_file is not None and os.path.exists(record_file):
            os.remove(record_file)

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, session, config, items):
        selection_file = config.getoption("selection-file")
        shuffle = config.getoption("shuffle")

        if self.record_file is None or selection_file is None:
            if shuffle:
                random.shuffle(items)

            return

        selection, remaining = make_selection(selection_file, items)
        self.record = {it.nodeid: [0, 0] for it in selection}

        if len(selection) == 0:
            pytest.exit("ShowFlakes: no tests selected", 1)

        max_runs = config.getoption("max-runs")
        max_fail = config.getoption("max-fail")
        max_time = config.getoption("max-time")
        n_extra = config.getoption("n-extra")

        gc.disable()

        while max_runs > 0 and max_fail > 0:
            if n_extra < len(remaining):
                items[:] = random.sample(remaining, n_extra) + selection

            if shuffle:
                random.shuffle(items)

            pid = os.fork()

            if pid == 0:
                return

            exitstatus = None
            proc = Process(pid=pid)

            if config.getoption("deprioritize"):
                tasks = set()

                if max_time is not None:
                    time_start = time.time()

                while exitstatus is None:
                    try:
                        exitstatus = proc.wait(timeout=0.01)
                    except TimeoutExpired:
                        deprioritize_tasks(proc, tasks)

                    if max_time is not None and (
                        time.time() - time_start >= max_time
                    ):
                        break
            else:
                try:
                    exitstatus = proc.wait(timeout=max_time)
                except TimeoutExpired:
                    pass

            if exitstatus != 0:
                if proc.is_running():
                    proc.kill()

                max_fail -= 1
                continue

            with open(self.record_file, "r") as fd:
                record_next = json.load(fd)

            if self.record == record_next:
                max_fail -= 1
                continue

            self.record.update(record_next)
            values = self.record.values()

            if any(0 < n_fail < n_runs for n_fail, n_runs in values):
                break

            max_runs -= 1

        if max_fail == 0:
            pytest.exit("ShowFlakes: reached fail limit", 1)

        pytest.exit("ShowFlakes: finished", 0)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtestloop(self, session):
        yield

        if self.record is not None:
            with open(self.record_file, "w") as fd:
                json.dump(self.record, fd, indent=4)

            os._exit(0)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item, nextitem):
        self.outcome = "passed"

        yield

        nid = item.nodeid
        
        if self.record is None:
            if self.record_file is not None:
                with open(self.record_file, "a") as fd:
                    fd.write(self.outcome + "\t" + nid + "\n")
        else:
            record_nid = self.record.get(nid, None)

            if record_nid is not None:
                record_nid[0] += self.outcome == "failed"
                record_nid[1] += self.outcome != "skipped"

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
        "--selection-file", action="store", dest="selection-file", type=str
    )

    group.addoption(
        "--max-runs", action="store", default=1, dest="max-runs", type=int
    )

    group.addoption(
        "--max-fail", action="store", default=1, dest="max-fail", type=int
    )

    group.addoption(
        "--max-time", action="store", dest="max-time", type=int
    )

    group.addoption(
        "--n-extra", action="store", default=0, dest="n-extra", type=int
    )

    group.addoption(
        "--shuffle", action="store_true", dest="shuffle"
    )

    group.addoption(
        "--deprioritize", action="store_true", dest="deprioritize"
    )

    group.addoption(
        "--mock-flaky", action="store_true", dest="mock-flaky"
    )

    group.addoption(
        "--set-exitstatus", action="store_true", dest="set-exitstatus",
    )


def pytest_configure(config):
    record_file = config.getoption("record-file")
    config.pluginmanager.register(ShowFlakes(record_file))

    if config.getoption("mock-flaky"):
        config.addinivalue_line(
            "markers", 
            "flaky: marks tests to be automatically retried upon failure"
        )