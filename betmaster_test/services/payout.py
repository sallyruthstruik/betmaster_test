import logging
from decimal import Decimal

from betmaster_test.exceptions import BetmasterError
from betmaster_test.models import Transaction, Wallet, TransactionTypes, TransactionStatus
from betmaster_test.payment_systems import PaymentService, Payout


logger = logging.getLogger("payout")


class PayoutService:
    def __init__(self, api: PaymentService):
        self.api = api

    def begin_payout(self, wallet: Wallet, amount: Decimal):
        """
        Создает заявку на вывод средств в стороннюю платежную систему
        """
        tr = Transaction.objects.create(
            wallet=wallet,
            type=TransactionTypes.PAYOUT,
            amount=amount,
        )

        logger.info("создана заявка на вывод средств: %s", tr)
        return tr

    def send_payout_request_to_api(self, tr: Transaction):
        if tr.status != TransactionStatus.NEW:
            raise BetmasterError("некорректный статус транзакции", transaction=tr)

        resp = self.api.payout(Payout(
            description=tr.description,
            amount=tr.amount,
            currency=tr.wallet.currency.name,
            wallet_id=tr.wallet.wallet_id,
            merchant_id=tr.id,
        ))

        # сохраняем id в сторонней системе
        tr.payment_system_id = resp.transaction_id
        tr.status = TransactionStatus.PROCESSING
        tr.save()

        logger.info("заявка на вывод отправлена во внешний сервис: %s", tr)
