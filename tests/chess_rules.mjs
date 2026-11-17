import assert from 'node:assert/strict';
import {Chess} from '../frontend/vendor/chess/chess.js';
import {chooseMove} from '../frontend/chess-ai.js';
function perft(game,depth){if(!depth)return 1;let nodes=0;for(const move of game.moves()){game.move(move);nodes+=perft(game,depth-1);game.undo();}return nodes;}
const initial=new Chess();assert.equal(perft(initial,1),20);assert.equal(perft(initial,2),400);assert.equal(perft(initial,3),8902);
const castle=new Chess('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1');castle.move('O-O');assert.equal(castle.get('g1').type,'k');assert.equal(castle.get('f1').type,'r');
const attacked=new Chess('r3k2r/8/8/8/8/8/5r2/R3K2R w KQkq - 0 1');assert(!attacked.moves().includes('O-O'));
const ep=new Chess('4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1');ep.move({from:'e5',to:'d6'});assert.equal(ep.get('d5'),undefined);assert.equal(ep.get('d6').type,'p');
const promo=new Chess('7k/P7/8/8/8/8/8/7K w - - 0 1');promo.move({from:'a7',to:'a8',promotion:'n'});assert.equal(promo.get('a8').type,'n');
const mate=new Chess();for(const move of ['f3','e5','g4','Qh4#'])mate.move(move);assert(mate.isCheckmate());
const stale=new Chess('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1');assert(stale.isStalemate());assert.equal(chooseMove(stale.fen()).move,null);
const repeat=new Chess();for(let i=0;i<2;i++)for(const move of ['Nf3','Nf6','Ng1','Ng8'])repeat.move(move);assert(repeat.isThreefoldRepetition());
assert(new Chess('7k/8/8/8/8/8/8/R6K w - - 100 1').isDrawByFiftyMoves());assert(new Chess('7k/8/8/8/8/8/8/7K w - - 0 1').isInsufficientMaterial());
for(const level of [1,2,3]){const state=new Chess(),fen=state.fen(),reply=chooseMove(fen,level,{budget:250});assert(state.move(reply.move));assert.equal(state.history().length,1);}
const tactical=new Chess('7k/5Q2/6K1/8/8/8/8/8 w - - 0 1');const winning=chooseMove(tactical.fen(),2,{budget:800});tactical.move(winning.move);assert(tactical.isCheckmate());
console.log('PASS: legal opening move counts, both castling placement and attack restriction, en passant, underpromotion, mate/stalemate, repetition/fifty-move/insufficient-material draws; bounded local opponent returns legal moves and finds mate.');
