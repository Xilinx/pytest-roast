#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import re
from warnings import warn
from pathlib import Path
import pytest
from _pytest.mark.legacy import matchkeyword
from typing import List, Optional
from config import ConfigurationSet, InterpolateEnumType
from roast.confParser import generate_conf
from roast.component.basebuild import Basebuild
from roast.component.scenario import scenario, Scenario
from roast.component.board.board import Board
from roast.utils import overrides, has_key, filter_keys, load_yaml, filter_dict


def pytest_addoption(parser):
    parser.addoption("--override", action="store", nargs="+", type=str, default="")
    parser.addoption("--select", action="store", nargs="+", type=str, default=None)
    parser.addoption(
        "--select_filter", action="store", nargs="+", type=str, default=None
    )
    parser.addoption("--unselect", action="store", nargs="+", type=str, default=None)
    parser.addoption(
        "--unselect_filter", action="store", nargs="+", type=str, default=None
    )
    parser.addoption("--machine", action="store", nargs="+", type=str, default=None)


def pytest_collection_modifyitems(session, config, items):

    for option_name, should_select in [("select", True), ("unselect", False)]:
        is_file = False
        select_expr = config.getoption(option_name)
        filter_list = config.getoption(f"{option_name}_filter")
        if select_expr is None:
            continue

        # Search for file based on '.' presence.
        if "." in "".join(select_expr):
            selection_file_path = Path("".join(select_expr))
            if selection_file_path.exists() and selection_file_path.is_file():
                is_file = True

                if str(selection_file_path).endswith(".json") or str(
                    selection_file_path
                ).endswith(".yaml"):

                    filter_keys = filter_keys(filter_list)
                    test_data = load_yaml(selection_file_path)
                    test_list = filter_dict(test_data, filter_keys)
                    test_names = {test_name.strip() for test_name in test_list}

                else:

                    with selection_file_path.open(
                        "r", encoding="UTF-8"
                    ) as selection_file:
                        test_names = {test_name.strip() for test_name in selection_file}

        mystr = str(" ".join(select_expr))
        # Check for regex in string
        is_regex = not (all((re.escape(i) == i) for i in "".join(mystr.split())))

        seen_test_names = set()
        selected_items = []
        deselected_items = []
        for item in items:
            if is_file:
                if item.name in test_names or item.nodeid in test_names:
                    selected_items.append(item)
                else:
                    deselected_items.append(item)
            else:
                mysrch = re.compile(mystr)
                if is_regex:
                    if mysrch.search(str(item.name)) and mysrch.search(item.nodeid):
                        selected_items.append(item)
                    else:
                        deselected_items.append(item)

                else:
                    if matchkeyword(item, mystr):
                        selected_items.append(item)
                    else:
                        deselected_items.append(item)

            seen_test_names.add(item.name)
            seen_test_names.add(item.nodeid)

        if not should_select:
            # We are deselecting, flip collections
            selected_items, deselected_items = deselected_items, selected_items

        # Slice assignment is required since `items` needs to be modified in place
        items[:] = selected_items
        config.hook.pytest_deselected(items=deselected_items)


def pytest_configure(config):
    config.cache.set("override", config.getoption("override"))
    config.cache.set("machine", config.getoption("machine"))
    pytest.override = config.getoption("override")
    pytest.machine = config.getoption("machine")


@pytest.fixture
def get_cmdl_machine_opt(request):
    machine = request.config.cache.get("machine", None)
    if machine:
        return machine[0].split(",")
    else:
        return None


@pytest.fixture
def create_configuration(request):
    def _cfg(
        test_name: str = None,
        base_params: Optional[List[str]] = None,
        params: Optional[List[str]] = None,
        overrides: Optional[List[str]] = None,
        machine: str = "",
        interpolate_type=InterpolateEnumType.STANDARD,
    ) -> ConfigurationSet:
        rootdir = request.config.rootdir.strpath
        fspath = request.node.fspath
        if test_name is None:
            test_name = get_test_name(request.node.name)
        if overrides is None:
            overrides = request.config.cache.get("override", None)
        return generate_conf(
            rootdir,
            fspath,
            test_name,
            base_params=base_params,
            params=params,
            overrides=overrides,
            machine=machine,
            interpolate_type=interpolate_type,
        )

    return _cfg


def get_test_name(fname):
    fname = str(fname).split("[")[0]
    fname = fname.replace("build_", "")
    fname = fname.replace("run_", "")
    fname = fname.replace("test_", "")
    return fname


@pytest.fixture
def create_scenario(create_configuration):
    def _scenario(
        test_name: str = None,
        base_params: Optional[List[str]] = None,
        params: Optional[List[str]] = None,
        machine: str = "",
        interpolate_type=InterpolateEnumType.STANDARD,
    ) -> Scenario:
        config = create_configuration(
            test_name=test_name,
            base_params=base_params,
            params=params,
            machine=machine,
            interpolate_type=interpolate_type,
        )
        return scenario(config)

    return _scenario


# Fixtures for board
# This fixture preserves board throughout the session
@pytest.fixture(scope="session")
def host_board_session():
    board_obj = Board("host_target").driver
    yield board_obj


@pytest.fixture(scope="session")
def network_board_session():
    board_obj = Board("network_target").driver
    yield board_obj


@pytest.fixture(scope="session")
def systest_board_session():
    try:
        board_obj = Board("systest").driver
        yield board_obj
    except:
        yield None


@pytest.fixture(scope="function")
def get_board(
    request,
    host_board_session,
    network_board_session,
    systest_board_session,
    create_configuration,
):
    config = create_configuration()
    warn(
        "The 'get_board' fixture will be deprecated in 2.0. Try the 'board' fixture that doesn't call Basebuild.",
        category=DeprecationWarning,
    )

    def _board(
        board_type=config.get("board_interface"),
        reboot=True,
        xsdb=True,
        hwserver=True,
        interface=None,
        test_name=None,
        base_params=None,
        params=None,
        machine=None,
        override=None,
    ):
        config = create_configuration(
            test_name=test_name, base_params=base_params, params=params, machine=machine
        )
        bb = Basebuild(config, setup=False)
        bb.configure()
        if override is not None:
            config = overrides(config, override)
        if board_type == "network_target":
            sboard = network_board_session
        elif board_type == "host_target":
            sboard = host_board_session
        elif board_type == "systest":
            sboard = systest_board_session
        else:
            raise Exception(f"Board type {board_type} is not supported.")
        sboard.config = config
        sboard.reboot = reboot
        if sboard.serial:
            sboard.serial.mode = reboot
        sboard.invoke_xsdb = xsdb
        sboard.invoke_hwserver = hwserver
        if interface:
            sboard.config["board_interface"] = interface
        sboard.start()
        return sboard

    return _board


@pytest.fixture(scope="function")
def board(
    request,
    host_board_session,
    network_board_session,
    systest_board_session,
    create_configuration,
):
    config = create_configuration()

    def _board(
        board_type=config.get("board_interface"),
        reboot=True,
        xsdb=True,
        hwserver=True,
        interface=None,
        test_name=None,
        base_params=None,
        params=None,
        machine=None,
    ):
        config = create_configuration(
            test_name=test_name, base_params=base_params, params=params, machine=machine
        )
        if board_type == "network_target":
            sboard = network_board_session
        elif board_type == "host_target":
            sboard = host_board_session
        elif board_type == "systest":
            sboard = systest_board_session
        else:
            raise Exception(f"Board type {board_type} is not supported.")
        sboard.config = config
        sboard.reboot = reboot
        if sboard.serial:
            sboard.serial.mode = reboot
        sboard.invoke_xsdb = xsdb
        sboard.invoke_hwserver = hwserver
        if interface:
            sboard.config["board_interface"] = interface
        sboard.start()
        return sboard

    return _board


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    from pytest import ExitCode

    no_tests_collected = ExitCode.NO_TESTS_COLLECTED
    tests_failed = ExitCode.TESTS_FAILED
    ok = ExitCode.OK

    if exitstatus == no_tests_collected:
        session.exitstatus = ok


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """ Called to perform the setup phase for a test item. """
    print(f"\nTest: {item.name} Started...\n")


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item, nextitem):
    """ Called to perform the teardown phase for a test item. """
    print(f"\nTest: {item.name} Finished...\n")
