from django.test import Client
from django.urls import reverse

from betmaster_test.models import PaymentSystem, TransactionStatus, Transaction
from tests.fixtures import CommonFixtures


def test_begin_deposit_validation(client: Client, fixtures: CommonFixtures):
    resp = client.post(reverse("begin_deposit"))
    assert resp.status_code == 400

    resp = client.post(reverse("begin_deposit"), data={
        "payment_system": "test",
        "amount": 123,
        "wallet_id": fixtures.wallet_rub.id,
    })
    assert resp.status_code == 400


def test_deposit(client: Client, fixtures: CommonFixtures, mock_send_task):
    resp = client.post(reverse("begin_deposit"), data={
        "payment_system": PaymentSystem.SUPERPAY.value,
        "amount": 123,
        "wallet_id": fixtures.wallet_rub.id,
    })
    assert resp.status_code == 200

    tr_id = resp.json()["transaction_id"]
    resp = client.get(reverse("get_deposit_status", kwargs={"transaction_id": tr_id}))
    assert resp.status_code == 200
    assert resp.json() == {'id': 1, 'redirect_url': 'dummy!', 'status': TransactionStatus.PROCESSING}

    fixtures.wallet_rub.refresh_from_db()
    assert fixtures.wallet_rub.balance == 1000

    # callback
    tr = Transaction.objects.get(id=tr_id)
    resp = client.get(reverse('redirect_success_callback', kwargs={"hash": tr.secret_hash}))
    assert resp.status_code == 200

    fixtures.wallet_rub.refresh_from_db()
    assert fixtures.wallet_rub.balance == 1123
