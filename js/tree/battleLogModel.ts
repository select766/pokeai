export type StatusKeys5 = 'atk' | 'def' | 'spa' | 'spd' | 'spe';
export type StatusKeys6 = 'hp' | StatusKeys5;

export type PartyPoke = {
  name: string;
  species: string;
  moves: string[];
  ability: string;
  evs: { [key in StatusKeys6]: number };
  ivs: { [key in StatusKeys6]: number };
  item: string;
  level: number;
  shiny: boolean;
  gender: string;
  nature: string;
};

export type Party = PartyPoke[];

export type Player = {
  player_id: string;
  party: Party;
};

export type PlayerKeys = 'p1' | 'p2';

export type BattleEventUpdate = {
  type: 'update';
  update: string[];
};

export type PossibleAction = {
  simulator_key: string;
  poke: string; // 'slowbro'
  move: string;
  switch: boolean;
  force_switch: boolean;
  allMoves: string[];
  item: string;
};

export type Weather = 'none';

export type NonVolatileStatus = '' | 'psn' | 'tox' | 'brn' | 'par' | 'slp' | 'frz';

export type ActiveStatus = {
  pokemon: string; // "p1a: Corsola"
  species: string; // "Corsola"
  level: number;
  gender: string;
  hp_current: number;
  hp_max: number;
  status: NonVolatileStatus;
  ranks: { [key in StatusKeys5 | 'accuracy' | 'evasion']: number };
  volatile_statuses: string[];
};

export type SideStatus = {
  active: ActiveStatus; // 場に出ているポケモンの状態
  side_statuses: string[]; // プレイヤーの場の状態
  total_pokes: number;
  remaining_pokes: string;
};

export type BattleStatus = {
  side_friend: PlayerKeys;
  side_opponent: PlayerKeys;
  side_party: Party;
  turn: number;
  weather: Weather;
  side_statuses: { [key in PlayerKeys]: SideStatus };
};

export type BattleRequestSidePokemon = {
  ident: string; // "p2: Crobat"
  details: string; // "Crobat, L55, M"
  condition: string; // "209/209"
  active: boolean;
  stats: { [key in StatusKeys5]: number };
  moves: string[]; // ["return102", "steelwing", "swift", "takedown"]
  baseAbility: string;
  item: string;
  pokeball: string;
};

export type BattleRequest = {
  active: [{
    moves: {
      move: string;// "Return 102"
      id: string;//"return"
      pp: number;
      maxpp: number;
      target: string;
      disabled: boolean;
    }[];
  }];
  side: {
    name: PlayerKeys;
    id: PlayerKeys;
    pokemon: BattleRequestSidePokemon[];
  }
}

export interface BattleSearchLogEntry {
  type: string;
  payload: any;
}

export type BattleEventChoice = {
  type: 'choice';
  choice: {
    player: PlayerKeys;
    // possible_actions?: PossibleAction[]; //選択肢が1つしかない場合は存在しない
    // q_func?: { // モデルで思考していない場合は存在しない
    //   q_func: (number|null)[];
    //   action: number;
    // };
    // battle_status: BattleStatus;
    request: BattleRequest;
    choice: string;
    searchLog?: BattleSearchLogEntry[];
    searchTime?: number;
  }
};

export type BattleEvent = BattleEventUpdate | BattleEventChoice;

export type BattleLog = {
  agents: { [key in PlayerKeys]: Player };
  events: BattleEvent[];
  end: {
    winner: PlayerKeys | ''; // '': 引き分け
  }
};
