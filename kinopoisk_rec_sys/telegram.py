from typing import List
from attrs import define


@define(frozen=True)
class User:
    id: int
    preferred_categories: List[str]


class KinopoiskBot:
    def __init__(self):
        ...

    def catch_user_request(self):
        ...


if __name__ == '__main__':
    k = KinopoiskBot()
