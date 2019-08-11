import enum
from enum import Enum, IntEnum

from django.db import models
from django.urls import reverse


class ReprMixin:
    def __repr__(self):
        attrs = ", ".join([
            f"{k}={v!r}"
            for k, v in self.__dict__.items()
            if k[0] != "_"
        ])
        return f"{self.__class__.__name__}({attrs})"

    def __unicode__(self):
        return self.__repr__()

    def __str__(self):
        return self.__repr__()


class EnumChoicesMixin:
    @classmethod
    def choices(cls):
        return [
            (item.value, fieldname)
            for fieldname, item in cls.__dict__.items()
            if isinstance(item, cls)
        ]


@enum.unique
class UserLocales(EnumChoicesMixin, str, Enum):
    EN = "en"
    RU = "ru"


class User(models.Model, ReprMixin):
    # pylint: disable=fixme
    # TODO: связать со встроенной моделью django.User

    name = models.CharField(max_length=256)
    email = models.EmailField(unique=True)
    locale = models.CharField(
        max_length=2, choices=UserLocales.choices(),
        default=UserLocales.RU,
    )


class Currency(models.Model, ReprMixin):
    """
    Валюта пользователя
    """
    name = models.CharField(max_length=3, unique=True)
    value_usd = models.DecimalField(max_digits=10, decimal_places=2)    # курс валюты к USD


class Wallet(models.Model, ReprMixin):
    """
    Кошелек пользователя
    """
    user = models.ForeignKey(User, blank=False, related_name="wallets", on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, blank=False, related_name="wallets", on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    wallet_id = models.IntegerField()       # id кошелька во внешней системе

@enum.unique
class TransactionTypes(EnumChoicesMixin, str, Enum):
    DEPOSIT = "deposit"
    PAYOUT = "payout"


@enum.unique
class TransactionStatus(EnumChoicesMixin, str, Enum):
    NEW = "new"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class PaymentSystem(EnumChoicesMixin, str, Enum):
    SUPERPAY = "superpay"


class Transaction(ReprMixin, models.Model):
    """
    Представляет одну транзакцию (снятие или депозит)
    """
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TransactionTypes.choices())
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(default=TransactionStatus.NEW, max_length=256)
    description = models.CharField(max_length=1000)

    # ссылка на шлюз для проведения оплаты.
    # Ссылка предоставляется сторонней платежной системой
    redirect_url = models.URLField(blank=True)

    # платежная система. В будущем можно вынести в модель
    payment_system = models.CharField(max_length=100, choices=PaymentSystem.choices())

    # хэш используется в колбэке. Это безопаснее чем целочисленный id
    secret_hash = models.CharField(max_length=256, unique=True)

    def get_redirect_success_url(self):
        """
        Возвращает URL success-колбэка.
        """
        return reverse("redirect_success_callback", kwargs=dict(hash=self.secret_hash))

    def get_redirect_failure_url(self):
        """
        Возвращает URL failure-колбэка.
        """
        return reverse("redirect_failure_callback", kwargs=dict(hash=self.secret_hash))
