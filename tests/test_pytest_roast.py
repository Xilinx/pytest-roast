#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import pytest
from pytest_cases import parametrize_with_cases, parametrize
from roast.component.board.board import Board
from roast.component.board.target_board import TargetBoard
from config import InterpolateEnumType


@pytest.fixture
def setup_env(request):
    rootdir = request.config.rootdir.strpath
    yield
    os.chdir(rootdir)


@parametrize(i=range(2))
def case_from_cache(i, get_cmdl_machine_opt):
    return get_cmdl_machine_opt[i]


@parametrize_with_cases("machine", cases=".")
def test_create_configuration(request, create_configuration, machine, mocker):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = request.node.name
    mock_generate_conf = mocker.patch("pytest_roast.generate_conf")
    create_configuration(test_name=test_name, machine=machine)
    mock_generate_conf.assert_called_with(
        rootdir,
        fspath,
        test_name,
        base_params=None,
        params=None,
        overrides=["tests/main/conf.py"],
        machine=machine,
        interpolate_type=InterpolateEnumType.STANDARD,
    )


def test_create_scenario(create_scenario, mocker):
    conf = {"roast.testsuite": "testsuite", "roast.system": "system"}
    mocker.patch("pytest_roast.generate_conf", return_value=conf)
    mock_scenario = mocker.patch("pytest_roast.scenario")
    create_scenario()
    mock_scenario.assert_called_with(conf)


def test_board_session_fixture(host_board_session):
    b = host_board_session
    assert isinstance(b, TargetBoard)


def test_board_fixture(board, mocker):
    mocker.patch.object(TargetBoard, "start")
    b = board(board_type="network_target")
    assert isinstance(b, TargetBoard)
    bb = board(board_type="host_target")
    assert isinstance(bb, TargetBoard)


def test_get_board_fixture(request, get_board, mocker, setup_env):
    mocker.patch.object(TargetBoard, "start")
    b = get_board(board_type="network_target")
    assert isinstance(b, TargetBoard)
    os.chdir(request.config.rootdir.strpath)
    bb = get_board(board_type="host_target")
    assert isinstance(bb, TargetBoard)


def test_board_exception(board, mocker):
    mocker.patch.object(TargetBoard, "start")
    with pytest.raises(Exception):
        b = board()


def test_get_board_exception(get_board, mocker):
    mocker.patch.object(TargetBoard, "start")
    with pytest.raises(Exception):
        bb = get_board()
