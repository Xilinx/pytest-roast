#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from warnings import warn
import pytest
from typing import List, Optional
from config import ConfigurationSet, InterpolateEnumType
from roast.confParser import generate_conf
from roast.component.basebuild import Basebuild
from roast.component.scenario import scenario, Scenario
from roast.component.board.board import Board


def pytest_addoption(parser):
    parser.addoption("--override", action="store", nargs="+", type=str, default="")
    parser.addoption("--machine", action="store", nargs="+", type=str, default=None)


def pytest_configure(config):
    pytest.override = (
        config.getoption("override") if config.getoption("override") else []
    )
    pytest.machine = (
        config.getoption("machine")[0] if config.getoption("machine") else None
    )


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
            overrides = pytest.override
        else:
            overrides = overrides + pytest.override
        if machine == "":
            machine = pytest.machine
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
        overrides: Optional[List[str]] = None,
        machine: str = "",
        interpolate_type=InterpolateEnumType.STANDARD,
    ) -> Scenario:
        config = create_configuration(
            test_name=test_name,
            base_params=base_params,
            params=params,
            overrides=overrides,
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
        "The 'get_board' fixture has been deprecated. Migrate to the 'board' fixture that doesn't call Basebuild.",
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
        overrides=None,
    ):
        config = create_configuration(
            test_name=test_name,
            base_params=base_params,
            params=params,
            overrides=overrides,
            machine=machine,
        )
        Basebuild(config, setup=False)
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
        overrides=None,
    ):
        config = create_configuration(
            test_name=test_name,
            base_params=base_params,
            params=params,
            overrides=overrides,
            machine=machine,
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
