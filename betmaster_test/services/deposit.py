"""
Модуль позволяет проводить пополнение внутреннего кошелька системы (:class:`.Wallet`)
через сторонние платежные системы

Обычно сторонние системы работают по следующей схеме:

1. Отправляется запрос на оплату в стороннюю систему
2. Система возвращает redirect_url на страницу оплаты
3. Пользователь переходит на страницу оплаты, проводит оплату
4. В случае успеха система дергает success_url нашего сервера, в случае неудачи - error_url

Timeline::


    Пользователь                     Наш сервер                 Сторонний шлюз для оплаты

                        POST /deposit
    Инициирует запрос ----------------->
                                                (1) POST /api/deposit
                                        ------------------------------------>

                                                (2) возвращает redirect_url
                                        <------------------------------------
                    (2) возвращаем
                    redirect_url
                    пользователю
            <----------------------------

                (3) пользователь идет по redirect_url,
                попадает на страницу оплаты
            ----------------------------------------------------------------->

                                                (4) пользователь провел
                                                оплату,
                                                шлюз редиректит его на наш
                                                success/errorcallback
                                        <-------------------------------------



Пополнение считается завершенным если мы получили success callback от внешней системы

"""
import hashlib
import logging
from decimal import Decimal

from django.db import transaction

from betmaster_test import models, settings
from betmaster_test.exceptions import BetmasterError
from betmaster_test.models import Wallet, TransactionTypes, PaymentSystem, Transaction
from betmaster_test.payment_systems import PaymentService, Deposit
from betmaster_test.payment_systems.superpay import SuperPayService

logger = logging.getLogger("deposit_service")


class DepositService:
    def __init__(self, api: PaymentService):
        self.api = api

    @classmethod
    def for_payment_system(cls, name: str) -> "DepositService":
        if name == PaymentSystem.SUPERPAY:
            return DepositService(SuperPayService())
        raise BetmasterError("неизвестная платежная система", name=name)

    @classmethod
    def _generate_hash(cls, transaction_id: int):
        return hashlib.sha256(f"{settings.SECRET_KEY}:{transaction_id}".encode("utf8")).hexdigest()

    @classmethod
    def begin_deposit(cls, wallet: Wallet, amount: Decimal) -> models.Transaction:
        """
        Создает заявку на вывод в базе
        """
        assert amount > 0

        tr = models.Transaction.objects.create(
            wallet=wallet,
            type=TransactionTypes.DEPOSIT,
            amount=amount,
        )
        logger.info("создана новая заявка на оплату: %s", tr)
        return tr

    def send_deposit_request_to_api(self, tr: models.Transaction) -> str:
        """
        Отправляет заявку на депозит во внешнюю систему.
        Ждет ответа от системы и возвращает redirect_url
        куда должен перейти пользователь для оплаты
        """
        if tr.status != models.TransactionStatus.NEW:
            raise BetmasterError("некорректный статус транзакции", transaction=tr)

        tr.secret_hash = self._generate_hash(tr.id)

        response = self.api.deposit(Deposit(
            description=tr.description,
            amount=tr.amount,
            locale=tr.wallet.user.locale,
            merchant_id=tr.id,
            redirect_success_url=f"{settings.EXTERNAL_HOST}{tr.get_redirect_success_url()}",
            redirect_failure_url=f"{settings.EXTERNAL_HOST}{tr.get_redirect_failure_url()}",
            currency=tr.wallet.currency.name,
        ))
        tr.status = models.TransactionStatus.PROCESSING
        tr.redirect_url = response.redirect_url
        tr.save()

        logger.info("заявка отправлена в сторонний api: %s", tr)
        return response.redirect_url


@transaction.atomic
def background_task_send_deposit_to_api(payment_service: str, transaction_id: int):
    """
    Background задача для отправки запроса на депозит в стороннюю систему
    """
    ds = DepositService.for_payment_system(payment_service)
    tr = Transaction.objects.get(id=transaction_id)
    ds.send_deposit_request_to_api(tr)
