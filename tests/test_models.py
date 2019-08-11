from betmaster_test import models
from betmaster_test.models import TransactionTypes
from tests.fixtures import CommonFixtures


def test_TransactionTypes():
    assert TransactionTypes.choices() == [
        ('deposit', "DEPOSIT"),
        ('payout', "PAYOUT"),
    ]


def test_fixtures_loaded(fixtures: CommonFixtures):
    assert models.User.objects.count() == 1
    assert models.Wallet.objects.count() == 2
    assert fixtures.wallet_rub.balance == 1000
    assert fixtures.wallet_usd.balance == 100
