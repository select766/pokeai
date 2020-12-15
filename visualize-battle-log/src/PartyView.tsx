import React from 'react';
import { Party } from "./model";
import { name2jp } from './name2jp';

export interface PartyViewProps {
  party: Party;
}

export function PartyView({ party }: PartyViewProps): React.ReactElement {
  return <div className="partyView">
    <table>
      <tbody>
        {party.map((poke, i) => <tr key={i}><td>{name2jp(poke.species)}</td><td>LV{poke.level}</td><td>{name2jp(poke.item)}</td><td>{poke.moves.map((move) => name2jp(move)).join(', ')}</td></tr>)}
      </tbody>
    </table>
  </div>
}
