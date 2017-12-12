# -*- coding:utf-8 -*-


class Party(object):
    def __init__(self, pokes):
        self.fighting_poke_idx = 0
        self.pokes = pokes

    def get_fighting_poke(self):
        return self.pokes[self.fighting_poke_idx]

    def change_fighting_poke(self, idx):
        """
        場に出ているポケモンを交代する
        下がるポケモンはvolatile状態がリセットされる
        """
        assert self.fighting_poke_idx != idx
        self.pokes[self.fighting_poke_idx].reset_volatile()
        self.fighting_poke_idx = idx

    @property
    def is_all_faint(self):
        for poke in self.pokes:
            if not poke.is_faint:
                return False
        return True

    def render(self, static_only=True):
        """
        パーティ構成を表示する
        :param static_only:
        :return:
        """
        assert static_only
        print("Party")
        for poke in self.pokes:
            poke.render(static_only=static_only)
