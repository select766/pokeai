from typing import TypeVar

from pokeai.sim import context
import pokeai.sim
from pokeai.sim.game_rng import GameRNGReason
from pokeai.sim.move_handler_context import MoveHandlerContext
from pokeai.sim.poke import Poke, PokeNVCondition
from pokeai.sim.poke_db import PokeDBMoveInfo


class MoveCalculator:
    """
    技の作用を計算しポケモンに適用する機構
    """
    attack_player: int
    attack_poke: Poke
    defend_poke: Poke
    field: TypeVar("pokeai.sim.Field")

    def __init__(self, attack_player: int, attack_poke: Poke, defend_poke: Poke, field: "pokeai.sim.field.Field"):
        self.attack_player = attack_player
        self.attack_poke = attack_poke
        self.defend_poke = defend_poke
        self.field = field

    def run(self, move_idx: int):
        movest = self.attack_poke.moves[move_idx]
        move = movest.move
        multi_turn_move_info = self.attack_poke.multi_turn_move_info
        self.field.put_record_other(f"技 {move.name}")
        if multi_turn_move_info is not None:
            # 連続技のときは前回と同じ技を選んでないといけない
            assert multi_turn_move_info.move is movest.move
        # TODO: PPチェック
        """
       状態異常・変化に関して、行動可能かチェック
       (原作ではここで技名表示、PP消費)
       命中判定
       - 技が有効かどうかチェック（タイプ相性、状態異常の相手への状態異常技など）
       - 命中率による判定
       技の発動
       追加効果の発動
       """

        """
        複数ターン技について
        あなをほる、はなびらのまい等複数ターン自動継続する技
        継続中はattack_poke.multi_turn_move_infoにその技の継続状態について設定
        状態異常等で行動不能・技が外れると終了
        行動可能チェックで失敗したときはmulti_turn_move_info.abort()を呼ぶ
        技のハンドラに対してこの情報を与える
        はかいこうせんは連続技ではなく、発動成功時に「反動」状態にして混乱等と同様の扱い
        """

        move_info = context.db.get_move_info(move)
        ctx = MoveHandlerContext()
        ctx.attack_player = self.attack_player
        ctx.attack_poke = self.attack_poke
        ctx.defend_poke = self.defend_poke
        ctx.field = self.field
        ctx.move = move
        ctx.flag = move_info.flag

        if not self._check_can_move(move_info, ctx):
            """
            行動不能につき失敗
            """
            self.field.put_record_other("行動不能のため失敗")
            if multi_turn_move_info is not None:
                multi_turn_move_info.abort(self.attack_poke)
                self.attack_poke.multi_turn_move_info = None
            return

        if not self._check_hit(move_info, ctx):
            """
            技が外れた
            """
            self.field.put_record_other("発動条件・技が外れたため失敗")
            if multi_turn_move_info is not None:
                multi_turn_move_info.abort(self.attack_poke)
                self.attack_poke.multi_turn_move_info = None
            return

        self._launch_move(move_info, ctx)
        if self._check_side_effect(move_info, ctx):
            # 補助効果の発動
            self._launch_side_effect(move_info, ctx)

    def _check_can_move(self, move_info: PokeDBMoveInfo, ctx: MoveHandlerContext) -> bool:
        """
        行動可能チェック
        :param move:
        :return:
        """
        # 現状、選んだ技により成功失敗が変わることはない（第2世代のねごと等）
        # TODO: ねむり・こおり・まひ
        # TODO: こんらん
        if ctx.attack_poke.v_hyperbeam:
            self.field.put_record_other("反動でうごけない")
            ctx.attack_poke.v_hyperbeam = False
            return False
        if ctx.attack_poke.v_flinch:
            self.field.put_record_other("ひるみでうごけない")
            # ここでは解除せず、ターン終了で解除
            return False
        nv = ctx.attack_poke.nv_condition
        if nv is PokeNVCondition.FREEZE:
            self.field.put_record_other("こおりでうごけない")
            return False
        elif nv is PokeNVCondition.PARALYSIS:
            # 1/4で行動不能。
            r = ctx.field.rng.gen(ctx.attack_player, GameRNGReason.MOVE_PARALYSIS, 3)
            if r == 0:
                self.field.put_record_other("まひでうごけない")
                return False
        elif nv is PokeNVCondition.SLEEP:
            rem_turn = ctx.attack_poke.sleep_remaining_turn - 1
            assert rem_turn >= 0
            ctx.attack_poke.sleep_remaining_turn = rem_turn
            if rem_turn == 0:
                self.field.put_record_other("目を覚ました、このターンは行動不能")
                ctx.attack_poke.update_nv_condition(PokeNVCondition.EMPTY)
            else:
                self.field.put_record_other("眠っていて動けない")
            return False
        return True

    def _check_hit(self, move_info: PokeDBMoveInfo, ctx: MoveHandlerContext) -> bool:
        """
        命中判定（発動条件、相性、命中率すべて考慮）
        :param move:
        :return:
        """
        return move_info.check_hit(ctx)

    def _launch_move(self, move_info: PokeDBMoveInfo, ctx: MoveHandlerContext):
        """
        技の発動
        :param move:
        :return:
        """
        move_info.launch_move(ctx)

    def _check_side_effect(self, move_info: PokeDBMoveInfo, ctx: MoveHandlerContext) -> bool:
        """
        補助効果の発動判定（発動条件、発動確率）
        :param move:
        :return:
        """
        return move_info.check_side_effect(ctx)

    def _launch_side_effect(self, move_info: PokeDBMoveInfo, ctx: MoveHandlerContext):
        """
        補助効果の発動
        :param move:
        :return:
        """
        move_info.launch_side_effect(ctx)
