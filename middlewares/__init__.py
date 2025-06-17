from loader import dp

from .checksub import BigBrother


if __name__ == "middlewares":
    dp.middleware.setup(BigBrother())
