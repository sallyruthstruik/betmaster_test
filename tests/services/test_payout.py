from decimal import Decimal
from unittest.mock import Mock

import pytest

from betmaster_test.exceptions import BetmasterError
from betmaster_test.models import TransactionStatus
from betmaster_test.payment_systems import Payout
from betmaster_test.payment_systems._base import PayoutResponse
from betmaster_test.services.payout import PayoutService
from tests.fixtures import CommonFixtures


@pytest.fixture()
def payment_service_mck():
    return Mock()


@pytest.fixture()
def payout_service(payment_service_mck):
    return PayoutService(payment_service_mck)


def test_begin_payout(fixtures: CommonFixtures, payout_service: PayoutService):
    tr = payout_service.begin_payout(fixtures.wallet_rub, Decimal(10))
    assert tr.status == TransactionStatus.NEW
    assert tr.id


def test_send_payout_request_to_api_calls_api(
        fixtures: CommonFixtures,
        payout_service: PayoutService,
        payment_service_mck: Mock,
):
    payment_service_mck.payout.return_value = PayoutResponse(transaction_id=123)
    tr = payout_service.begin_payout(fixtures.wallet_rub, Decimal(10))

    payout_service.send_payout_request_to_api(tr)

    tr.refresh_from_db()
    assert tr.status == TransactionStatus.PROCESSING.value
    assert tr.payment_system_id == 123
    assert payment_service_mck.payout.call_count == 1
    deposit = payment_service_mck.payout.call_args[0][0]
    assert deposit == Payout(
        description='',
        amount=Decimal('10'),
        merchant_id=tr.id,
        currency="RUB",
        wallet_id=123123123,
    )


def test_send_payout_request_to_api_accepts_only_new(
        fixtures: CommonFixtures,
        payout_service: PayoutService,
        payment_service_mck: Mock,
):
    tr = payout_service.begin_payout(fixtures.wallet_rub, Decimal(10))
    tr.status = TransactionStatus.PROCESSING

    with pytest.raises(BetmasterError):
        payout_service.send_payout_request_to_api(tr)

    assert payment_service_mck.deposit.call_count == 0
