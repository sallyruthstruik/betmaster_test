from betmaster_test.payment_systems import PaymentService, Deposit, DepositResponse, Payout
from betmaster_test.payment_systems._base import PayoutResponse


class SuperPayService(PaymentService):
    def deposit(self, data: Deposit) -> DepositResponse:
        return DepositResponse(
            redirect_url="dummy!"
        )

    def payout(self, data: Payout) -> PayoutResponse:
        return PayoutResponse(
            transaction_id=123,
        )
