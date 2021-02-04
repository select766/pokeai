import React from 'react';
import { Player } from "./model";
import { PartyView } from './PartyView';

export interface PlayerViewProps {
  player: Player;
}

export function PlayerView({ player }: PlayerViewProps): React.ReactElement {
  return <div className="playerView">
    <div>Player {player.player_id}</div>
    <PartyView party={player.party} />
  </div>
}
