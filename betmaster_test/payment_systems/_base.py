import abc
import typing
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Deposit:
    description: str
    amount: Decimal
    currency: str
    locale: str
    merchant_id: int
    redirect_failure_url: str
    redirect_success_url: str


@dataclass
class DepositResponse:
    redirect_url: str


@dataclass
class Payout:
    description: str
    amount: Decimal
    currency: str
    wallet_id: int
    merchant_id: int


@dataclass
class PayoutResponse:
    """
    TODO: пока непонятно как будет выглядеть ответ платежной системы.
        Полагаем там есть некоторый id
    """
    transaction_id: typing.Any


class PaymentService(metaclass=abc.ABCMeta):
    """
    Интерфейс апи платежной системы
    """

    @abc.abstractmethod
    def deposit(self, data: Deposit) -> DepositResponse:
        """
        Метод создает запрос на пополнение через платежную систему.
        """

    @abc.abstractmethod
    def payout(self, data: Payout) -> PayoutResponse:
        """
        Метод выводит деньги на стороннюю платежную систему
        """
