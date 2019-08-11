import logging
from decimal import Decimal

from django.db import transaction
from django.http import JsonResponse, Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404

from betmaster_test import workers
from betmaster_test.exceptions import BetmasterError
from betmaster_test.models import Transaction, Wallet
from betmaster_test.payment_systems import Deposit
from betmaster_test.services.callbacks import Callbacks
from betmaster_test.services.deposit import DepositService, background_task_send_deposit_to_api

logger = logging.getLogger("views")
callbacks = Callbacks()


@transaction.atomic
def redirect_success_callback(request, hash):
    tr = get_object_or_404(Transaction, secret_hash=hash)
    callbacks.success(tr)
    return JsonResponse({}, status=200)


@transaction.atomic
def redirect_failure_callback(request, hash):
    tr = get_object_or_404(Transaction, secret_hash=hash)
    callbacks.failure(tr)
    return JsonResponse({}, status=200)


def begin_deposit(request):
    """
    Создает запрос на пополнение кошелька.
    Отправка в платежную систему происходит асинхронно, поэтому клиент
    должен запрашивать метод get_deposit_info для получения ссылки redirect_url для оплаты

    Возвращает id Transaction записи в базе
    """

    # TODO: использовать contrib.auth для определения текущего пользователя и проверять что
    #  wallet_id принадлежит ему.
    #  Также стоит использовать тут django-rest-framework.
    try:
        payment_system = request.POST["payment_system"]
        wallet_id = request.POST["wallet_id"]
        amount = float(request.POST["amount"])
        service = DepositService.for_payment_system(payment_system)
    except (LookupError, BetmasterError) as e:
        logger.warning("ошибка валидации: data=%s, e=%s", request.POST, e)
        return HttpResponseBadRequest()

    tr = service.begin_deposit(
        wallet=get_object_or_404(Wallet, id=wallet_id),
        amount=Decimal(amount),
    )

    # отправляем обработку депозита как асинхронную задачу
    # это защитит нас от потенциальных зависаний стороннего сервиса
    workers.send_task(
        background_task_send_deposit_to_api,
        payment_service=payment_system,
        transaction_id=tr.id
    )

    return JsonResponse({"transaction_id": tr.id})


def get_deposit_status(request, transaction_id):
    """
    Возвращает информацию по депозиту

    Клиент должен запрашивать этот метод периодически, и при изменении статуса
        делать редирект на redirect_url для оплаты
    """

    tr = get_object_or_404(Transaction, id=transaction_id)
    return JsonResponse({
        "id": tr.id,
        "redirect_url": tr.redirect_url,
        "status": tr.status,
    })
