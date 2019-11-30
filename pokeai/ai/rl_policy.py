import chainer
import numpy as np
from logging import getLogger
import tempfile
import shutil
import os

from chainerrl.agents import A3C

from pokeai.ai.agent_builder import build_agent
from pokeai.ai.battle_status import BattleStatus
from pokeai.ai.common import get_possible_actions
from pokeai.ai.feature_extractor import FeatureExtractor
from pokeai.ai.random_policy import RandomPolicy

logger = getLogger(__name__)


class RLPolicy(RandomPolicy):
    """
    強化学習による方策
    """
    feature_extractor: FeatureExtractor
    agent_build_params: dict
    agent: A3C

    def __init__(self, feature_extractor: FeatureExtractor, agent_build_params: dict):
        """
        方策のコンストラクタ
        :param feature_extractor:
        :param agent:
        """
        super().__init__()
        self.feature_extractor = feature_extractor
        self.agent_build_params = agent_build_params
        self.agent = build_agent(agent_build_params, feature_extractor.get_dims())

    def choice_turn_start(self, battle_status: BattleStatus, request: dict) -> str:
        """
        ターン開始時の行動選択
        :param battle_status:
        :param request:
        :return: 行動。"move [1-4]|switch [1-6]"
        """
        choice_idxs, choice_keys, choice_vec = get_possible_actions(battle_status, request)
        if len(choice_idxs) == 1:
            return choice_keys[0]
        return self._choice_by_model(battle_status, choice_idxs, choice_keys, choice_vec)

    def choice_force_switch(self, battle_status: BattleStatus, request: dict) -> str:
        """
        強制交換時の行動選択
        :param battle_status:
        :param request:
        :return: 行動。"switch [1-6]"
        """
        choice_idxs, choice_keys, choice_vec = get_possible_actions(battle_status, request)
        if len(choice_idxs) == 1:
            return choice_keys[0]
        return self._choice_by_model(battle_status, choice_idxs, choice_keys, choice_vec)

    def _choice_by_model(self, battle_status: BattleStatus, choice_idxs, choice_keys, choice_vec):
        """
        モデルで各行動の優先度を出し、それに従い行動を選択する
        :param battle_status:
        :param choice_idxs:
        :param choice_keys:
        :return:
        """
        logger.info(f"choice of player {battle_status.side_friend}")
        feat = self.feature_extractor.transform(battle_status, choice_vec)
        logger.debug(f"feature: {feat.tolist()}")
        if self.train:
            action = self.agent.act_and_train(feat, 0.0)  # 0~17の番号
        else:
            action = self.agent.act(feat)
        for idx, key in zip(choice_idxs, choice_keys):
            if idx == action:
                chosen = key
                break
        else:
            raise ValueError(f"action number {action} is not valid choice.")
        logger.debug(f"chosen: {chosen}")
        return chosen

    def game_end(self, reward: float):
        if self.train:
            # done=Trueの場合はstateは使用されないので問題ない
            self.agent.stop_episode_and_train(None, reward, True)
        else:
            # LSTMなどの場合には呼び出しが必要
            self.agent.stop_episode()

    def __getstate__(self):
        # pickle.dumpで呼び出される
        # agentはdumpできないので、インスタンスの生成引数を別途dictに入れる
        # エラー例: AttributeError: Can't pickle local object 'Optimizer.setup.<locals>.OptimizerHookable'
        # 学習された重みはディレクトリに保存しそれをtarアーカイブ、バイナリ文字列として読んでpickleに保存
        d = self.__dict__.copy()
        del d['agent']
        dump_dir = tempfile.mkdtemp()  # /tmp/xyz
        agent_dump_dir = os.path.join(dump_dir, 'agent')  # /tmp/xyz/agent
        os.mkdir(agent_dump_dir)
        self.agent.save(agent_dump_dir)  # /tmp/xyz/agent/model.npz など
        tar_path_wo_ext = os.path.join(dump_dir, 'archive')
        tar_path = tar_path_wo_ext + '.tar'
        shutil.make_archive(tar_path_wo_ext, 'tar', agent_dump_dir)  # /tmp/xyz/archive.tar
        with open(tar_path, 'rb') as f:
            archive_data = f.read()  # /tmp/xyz/archive.tar の中身
        shutil.rmtree(dump_dir)
        d['agent_archive'] = archive_data
        return d

    def __setstate__(self, state):
        state_direct = state.copy()
        del state_direct['agent_archive']
        self.__dict__.update(state_direct)
        self.agent = build_agent(self.agent_build_params, self.feature_extractor.get_dims())
        dump_dir = tempfile.mkdtemp()  # /tmp/xyz
        tar_path = os.path.join(dump_dir, 'archive.tar')
        with open(tar_path, 'wb') as f:  # /tmp/xyz/archive.tar を作成
            f.write(state['agent_archive'])
        agent_dump_dir = os.path.join(dump_dir, 'agent')  # /tmp/xyz/agent
        shutil.unpack_archive(tar_path, agent_dump_dir)  # /tmp/xyz/agent/model.npz など
        self.agent.load(agent_dump_dir)
        shutil.rmtree(dump_dir)
