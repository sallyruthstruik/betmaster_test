from concurrent.futures import Future


def send_task(func, *args, **kwargs) -> Future:
    """
    Отправляет таск в очередь для обработки.
    Должен возвращать объект Future

    Можно например использовать celery+rabbitmq как брокера сообщений
    """
    raise NotImplementedError
