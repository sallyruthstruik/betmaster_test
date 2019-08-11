from decimal import Decimal
from unittest.mock import Mock

import pytest

from betmaster_test.exceptions import BetmasterError
from betmaster_test.models import TransactionStatus, UserLocales
from betmaster_test.payment_systems import DepositResponse, Deposit
from betmaster_test.services.deposit import DepositService
from tests.fixtures import CommonFixtures

from tests.testutils import MatchesPattern


@pytest.fixture()
def payment_service_mck():
    return Mock()


@pytest.fixture()
def deposit_service(payment_service_mck: Mock):
    return DepositService(payment_service_mck)


def test_begin_deposit(fixtures: CommonFixtures, deposit_service: DepositService):
    tr = deposit_service.begin_deposit(fixtures.wallet_rub, Decimal(10))
    assert tr.status == TransactionStatus.NEW
    assert tr.id


def test_send_deposit_request_to_api_calls_api(
        fixtures: CommonFixtures,
        deposit_service: DepositService,
        payment_service_mck: Mock,
):
    tr = deposit_service.begin_deposit(fixtures.wallet_rub, Decimal(10))

    payment_service_mck.deposit.return_value = DepositResponse(redirect_url="http://test.ru")

    resp = deposit_service.send_deposit_request_to_api(tr)

    tr.refresh_from_db()
    assert tr.status == TransactionStatus.PROCESSING.value
    assert tr.secret_hash
    assert payment_service_mck.deposit.call_count == 1
    assert resp == "http://test.ru"
    deposit = payment_service_mck.deposit.call_args[0][0]
    assert deposit == Deposit(
        description='',
        amount=Decimal('10'),
        locale=UserLocales.RU,
        merchant_id=tr.id,
        redirect_failure_url=MatchesPattern(f"https://example.com/api/callbacks/failure/{tr.secret_hash}"),
        redirect_success_url=MatchesPattern(f"https://example.com/api/callbacks/success/{tr.secret_hash}"),
        currency="RUB",
    )


def test_send_deposit_request_to_api_accepts_only_new(
        fixtures: CommonFixtures,
        deposit_service: DepositService,
        payment_service_mck: Mock,
):
    tr = deposit_service.begin_deposit(fixtures.wallet_rub, Decimal(10))
    tr.status = TransactionStatus.PROCESSING

    with pytest.raises(BetmasterError):
        deposit_service.send_deposit_request_to_api(tr)

    assert payment_service_mck.deposit.call_count == 0
