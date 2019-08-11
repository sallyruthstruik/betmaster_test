from dataclasses import dataclass

import factory
from factory.django import DjangoModelFactory

from betmaster_test import models
from betmaster_test.models import TransactionStatus, PaymentSystem, TransactionTypes


class UserFactory(DjangoModelFactory):
    name = factory.Sequence(lambda i: f"User {i}")
    email = factory.Sequence(lambda i: f"user{i}@test.ru")

    class Meta:
        model = models.User


class CurrencyFactory(DjangoModelFactory):
    class Meta:
        model = models.Currency


class WalletFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    currency = factory.SubFactory(CurrencyFactory)
    wallet_id = 123123123

    class Meta:
        model = models.Wallet


class TransactionFactory(DjangoModelFactory):
    amount = 10
    status = TransactionStatus.NEW
    description = factory.Sequence(lambda i: f"Тестовая транзакция {i}")
    payment_system = PaymentSystem.SUPERPAY

    secret_hash = factory.Sequence(lambda i: f"secret {i}")
    type = TransactionTypes.DEPOSIT

    class Meta:
        model = models.Transaction


@dataclass
class CommonFixtures:
    user: models.User
    wallet_rub: models.Wallet
    wallet_usd: models.Wallet


TEST_USD_RUB_RATE = 50


def load_fixtures() -> CommonFixtures:
    """
    Создаем пользователя
    Создаем ему 2 кошелька с разными валютами
    Создаем некоторое значение на балансе кошельков
    """

    user = UserFactory()

    wallet_rub = WalletFactory(
        user=user,
        currency__name="RUB",
        currency__value_usd=1/TEST_USD_RUB_RATE,
        balance=1000,
    )

    wallet_usd = WalletFactory(
        user=user,
        currency__name="USD",
        currency__value_usd=1,
        balance=100,
    )

    return CommonFixtures(
        user=user,
        wallet_rub=wallet_rub,
        wallet_usd=wallet_usd,
    )
