from unittest import mock

import pytest

from betmaster_test import models
from tests.fixtures import WalletFactory, load_fixtures


@pytest.fixture()
def fixtures(db):
    return load_fixtures()


@pytest.fixture()
def mock_send_task():
    def impl(func, *a, **k):
        func(*a, **k)

    with mock.patch("betmaster_test.workers.send_task") as send_task_mck:
        send_task_mck.side_effect = impl
        yield send_task_mck


@pytest.fixture()
def mock_superpay():
    with mock.patch("betmaster_test.payment_systems.superpay.SuperPayService") as mck:
        yield mck
