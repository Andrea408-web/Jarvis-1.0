/* Original scalable chess silhouettes with shaded ivory/titanium surfaces. */
const ns='http://www.w3.org/2000/svg';let serial=0;
const shapes={
 p:'M25 30C16 23 20 10 32 10C44 10 48 23 39 30L37 39L44 57H20L27 39Z',
 r:'M18 13H25V20H29V13H35V20H39V13H46V28L40 33L42 57H22L24 33L18 28Z',
 n:'M20 57C19 47 24 40 34 35L24 38L16 33L23 22L24 14L33 20L42 15C50 24 51 40 46 57Z',
 b:'M32 9C43 18 47 26 39 33L35 37L41 57H23L29 37L25 33C17 26 21 18 32 9Z',
 q:'M17 23L25 32L32 18L39 32L47 23L42 43L40 57H24L22 43Z',
 k:'M28 10H36V17H43V24H36V31C45 34 45 41 39 45L42 57H22L25 45C19 41 19 34 28 31V24H21V17H28Z'
};
function el(tag,attrs,parent){const n=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,String(v));parent?.append(n);return n;}
export function pieceSVG(piece){const svg=el('svg',{viewBox:'0 0 64 80','aria-hidden':'true',focusable:'false',class:'chess-piece-art'}),id='piece-'+(++serial),white=piece.color==='w',defs=el('defs',{},svg),gradient=el('linearGradient',{id,x1:0,y1:0,x2:1,y2:.3},defs);for(const [offset,color]of [[0,white?'#fff7df':'#74816a'],[.45,white?'#e7d4a5':'#34452e'],[1,white?'#a78c55':'#101b0e']])el('stop',{offset,'stop-color':color},gradient);el('ellipse',{cx:32,cy:72,rx:23,ry:5,fill:'#000',opacity:.25},svg);const body=el('g',{fill:'url(#'+id+')',stroke:white?'#82703f':'#9aa881','stroke-width':1.2,'stroke-linejoin':'round'},svg);el('path',{d:shapes[piece.type]},body);el('path',{d:'M22 56H42L47 65H17Z'},body);el('path',{d:'M17 64H47V70H17Z'},body);el('path',{d:'M20 67H44',fill:'none',stroke:white?'#fff7df':'#c0ca9d','stroke-width':1,opacity:.7},body);if(piece.type==='b')el('path',{d:'M34 15L27 29',stroke:white?'#8f7843':'#a7b78b','stroke-width':3,fill:'none'},svg);if(piece.type==='n'){el('circle',{cx:29,cy:26,r:1.8,fill:white?'#504827':'#e1d797'},svg);el('path',{d:'M42 23C46 34 44 43 39 49',stroke:white?'#fff6d9':'#9dac83','stroke-width':1.5,fill:'none',opacity:.7},svg);}if(piece.type==='q')for(const [cx,cy]of [[17,20],[32,15],[47,20]])el('circle',{cx,cy,r:3.3,fill:'url(#'+id+')',stroke:white?'#82703f':'#9aa881','stroke-width':1},svg);return svg;}
