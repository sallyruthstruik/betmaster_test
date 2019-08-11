

class BetmasterError(Exception):
    def __init__(self, msg, **context):
        raw_ctx = [
            f"{key}={value!r}"
            for key, value in context.items()
        ]
        super(BetmasterError, self).__init__(f"{msg} {', '.join(raw_ctx)}")
        self.context = context
