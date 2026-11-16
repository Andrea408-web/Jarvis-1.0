"""Synthetic fixed-weight GGUF for real browser inference tests, not a useful AI."""
import math,struct
from pathlib import Path

def write_model(path):
 def u32(x):return struct.pack('<I',x)
 def u64(x):return struct.pack('<Q',x)
 def string(x):
  raw=x.encode();return u64(len(raw))+raw
 def value(kind,x):
  if kind==4:return u32(x)
  if kind==5:return struct.pack('<i',x)
  if kind==6:return struct.pack('<f',x)
  if kind==7:return struct.pack('<?',x)
  if kind==8:return string(x)
  if kind==9:
   subtype,items=x;return u32(subtype)+u64(len(items))+b''.join(value(subtype,i) for i in items)
 tokens=['<unk>','<s>','</s>']+[f'<0x{i:02X}>' for i in range(256)]
 kv=[('general.architecture',8,'llama'),('general.name',8,'Synthetic runtime test'),('llama.context_length',4,2048),('llama.embedding_length',4,32),('llama.block_count',4,1),('llama.feed_forward_length',4,64),('llama.attention.head_count',4,4),('llama.attention.head_count_kv',4,4),('llama.rope.dimension_count',4,8),('llama.attention.layer_norm_rms_epsilon',6,1e-5),('tokenizer.ggml.model',8,'llama'),('tokenizer.ggml.tokens',9,(8,tokens)),('tokenizer.ggml.scores',9,(6,[0.0]*len(tokens))),('tokenizer.ggml.token_type',9,(5,[2,3,3]+[6]*256)),('tokenizer.ggml.bos_token_id',4,1),('tokenizer.ggml.eos_token_id',4,2),('tokenizer.ggml.unknown_token_id',4,0),('tokenizer.ggml.add_bos_token',7,True),('tokenizer.chat_template',8,"{% for message in messages %}{{ '<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>\n' }}{% endfor %}{% if add_generation_prompt %}{{ '<|im_start|>assistant\n' }}{% endif %}")]
 tensors=[('token_embd.weight',[32,len(tokens)]),('output_norm.weight',[32]),('output.weight',[32,len(tokens)]),('blk.0.attn_norm.weight',[32]),('blk.0.attn_q.weight',[32,32]),('blk.0.attn_k.weight',[32,32]),('blk.0.attn_v.weight',[32,32]),('blk.0.attn_output.weight',[32,32]),('blk.0.ffn_norm.weight',[32]),('blk.0.ffn_gate.weight',[32,64]),('blk.0.ffn_up.weight',[32,64]),('blk.0.ffn_down.weight',[64,32])]
 header=b'GGUF'+u32(3)+u64(len(tensors))+u64(len(kv))+b''.join(string(k)+u32(t)+value(t,v) for k,t,v in kv)
 data=bytearray()
 for name,dims in tensors:
  while len(data)%32:data.append(0)
  header+=string(name)+u32(len(dims))+b''.join(u64(x) for x in dims)+u32(0)+u64(len(data))
  # Deterministic ASCII output avoids invalid random UTF-8 in JSON streaming.
  weights=[1.0 if len(dims)==1 else .1 if name=='token_embd.weight' else (1.0 if i//32==68 else 0.0) if name=='output.weight' else 0.0 for i in range(math.prod(dims))]
  data.extend(struct.pack('<'+'f'*len(weights),*weights))
 header+=b'\0'*((-len(header))%32);Path(path).write_bytes(header+data)
 return Path(path)
