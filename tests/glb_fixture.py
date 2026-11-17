"""Small original multipart GLB for offline browser tests, not a production model."""
import json,math,struct

def make_glb():
 positions=[];normals=[];indices=[];rings=12;segments=24
 for y in range(rings+1):
  a=math.pi*y/rings
  for x in range(segments+1):
   b=2*math.pi*x/segments;p=(math.sin(a)*math.cos(b),math.cos(a),math.sin(a)*math.sin(b));positions.extend(p);normals.extend(p)
 for y in range(rings):
  for x in range(segments):
   a=y*(segments+1)+x;b=a+segments+1;indices.extend((a,b,a+1,a+1,b,b+1))
 arrays=[struct.pack('<'+'f'*len(positions),*positions),struct.pack('<'+'f'*len(normals),*normals),struct.pack('<'+'H'*len(indices),*indices)];binary=b'';views=[]
 for data in arrays:
  views.append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)});binary+=data;binary+=b'\0'*((-len(binary))%4)
 doc={'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':[0,1]}],'nodes':[{'name':'Testteil A','mesh':0,'translation':[-.75,0,0]},{'name':'Testteil B','mesh':0,'translation':[.75,0,0]}],'meshes':[{'primitives':[{'attributes':{'POSITION':0,'NORMAL':1},'indices':2,'material':0}]}],'materials':[{'pbrMetallicRoughness':{'baseColorFactor':[.7,.65,.2,1],'metallicFactor':.6,'roughnessFactor':.3}}],'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':[{'bufferView':0,'componentType':5126,'type':'VEC3','count':len(positions)//3,'min':[-1,-1,-1],'max':[1,1,1]},{'bufferView':1,'componentType':5126,'type':'VEC3','count':len(normals)//3},{'bufferView':2,'componentType':5123,'type':'SCALAR','count':len(indices)}]}
 encoded=json.dumps(doc).encode();encoded+=b' '*((-len(encoded))%4);return struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary
