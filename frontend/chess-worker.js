import {chooseMove} from './chess-ai.js';
self.onmessage=event=>{const {id,fen,level}=event.data;try{self.postMessage({id,...chooseMove(fen,level)});}catch(_){self.postMessage({id,error:'Der Schachzug konnte nicht berechnet werden.'});}};
