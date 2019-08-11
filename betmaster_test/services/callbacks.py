from django.db import transaction, connection

from betmaster_test import models
from betmaster_test.exceptions import BetmasterError
from betmaster_test.models import TransactionStatus, Wallet, TransactionTypes


class Callbacks:

    def success(self, tr: models.Transaction):
        """
        Метод должен вызываться в on_success колбэке от платежной системы

        Метод блокирует строку wallet, поэтому транзакция его вызывающая
        должна быть как можно короче
        """
        assert tr.type == TransactionTypes.DEPOSIT, "пока поддерживаем только депозиты"

        self.validate(tr)

        # блокируем wallet для дальнейшего изменения
        wallet = Wallet.objects.select_for_update().get(id=tr.wallet_id)
        wallet.balance += tr.amount
        wallet.save()

        tr.status = TransactionStatus.SUCCESS
        tr.save()

    def failure(self, tr: models.Transaction):
        """
        Метод должен вызываться в on_error колбэке платежной системы
        """
        self.validate(tr)

        tr.status = TransactionStatus.FAILED
        tr.save()

    def validate(self, tr: models.Transaction):
        if tr.status != TransactionStatus.PROCESSING:
            raise BetmasterError("некорректный статус транзакции", transaction=tr)

