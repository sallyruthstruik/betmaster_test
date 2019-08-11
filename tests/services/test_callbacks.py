import logging
import random
from concurrent.futures.thread import ThreadPoolExecutor

import pytest
from django.db import transaction, connection

from betmaster_test.exceptions import BetmasterError
from betmaster_test.models import TransactionStatus, TransactionTypes
from betmaster_test.services.callbacks import Callbacks
from tests.fixtures import CommonFixtures, TransactionFactory


@pytest.fixture()
def callbacks():
    return Callbacks()


def test_race_in_success_callback(
        fixtures: CommonFixtures,
        callbacks: Callbacks,
        transactional_db,
):
    """
    Выполняет много депозитов в 100 тредов.
    Проверяет что нет состояния гонки в
    пополнениях/списаниях баланса
    """

    pool = ThreadPoolExecutor(10)

    tasks = [
        random.randrange(1, 100, 1)
        for _ in range(100)
    ]
    total_amount = sum(tasks)
    old_value = fixtures.wallet_rub.balance

    @transaction.atomic()
    def work(amount):
        tr = TransactionFactory(
            wallet=fixtures.wallet_rub,
            status=TransactionStatus.PROCESSING,
            amount=amount,
            type=TransactionTypes.DEPOSIT,
        )
        callbacks.success(tr)

    list(pool.map(work, tasks))
    fixtures.wallet_rub.refresh_from_db()
    assert fixtures.wallet_rub.balance == old_value + total_amount


def test_success_callback(
        fixtures: CommonFixtures,
        callbacks: Callbacks,
):

    # должен принимать только PROCESSING транзакции
    tr = TransactionFactory(
        wallet=fixtures.wallet_rub,
    )
    with pytest.raises(BetmasterError):
        callbacks.success(tr)

    # должен увеличивать баланс
    assert fixtures.wallet_rub.balance == 1000
    tr = TransactionFactory(
        wallet=fixtures.wallet_rub,
        status=TransactionStatus.PROCESSING,
    )

    callbacks.success(tr)

    tr.refresh_from_db()
    assert tr.status == TransactionStatus.SUCCESS
    fixtures.wallet_rub.refresh_from_db()
    assert fixtures.wallet_rub.balance == 1010

    # второй вызов упадет с ошибкой и не изменит баланс
    with pytest.raises(BetmasterError):
        callbacks.success(tr)

    tr.refresh_from_db()
    assert tr.status == TransactionStatus.SUCCESS
    fixtures.wallet_rub.refresh_from_db()
    assert fixtures.wallet_rub.balance == 1010


def test_failure_callback(
        fixtures: CommonFixtures,
        callbacks: Callbacks,
):
    # должен принимать только PROCESSING транзакции
    tr = TransactionFactory(
        wallet=fixtures.wallet_rub,
    )
    with pytest.raises(BetmasterError):
        callbacks.success(tr)

    # должен менять статус, не должен менять баланс
    tr = TransactionFactory(
        wallet=fixtures.wallet_rub,
        status=TransactionStatus.PROCESSING,
    )

    callbacks.failure(tr)

    tr.refresh_from_db()
    assert tr.status == TransactionStatus.FAILED

    fixtures.wallet_rub.refresh_from_db()
    assert fixtures.wallet_rub.balance == 1000
