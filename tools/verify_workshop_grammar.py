"""Optional real llama.cpp grammar check. Binaries are development tools, not shipped.

Usage: python tools/verify_workshop_grammar.py CONVERTER VALIDATOR
CONVERTER reads a schema on stdin and writes json_schema_to_grammar(schema,true).
VALIDATOR is llama.cpp's test-gbnf-validator. Its exit status alone is insufficient:
the official executable also returns zero for rejected input, so inspect its text.
"""
import copy,json,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.workshop_schema import design_schema
from tests.test_workshop_contours import RAW

def prepared(value):
 if isinstance(value,float):return round(value,5)
 if isinstance(value,list):return [prepared(v)for v in value]
 if isinstance(value,dict):return {k:prepared(v)for k,v in value.items()}
 return value

def ordered(value):
 value=prepared(value)
 if 'parts'in value:
  value['parts']=[{k:p[k]for k in ['name','shape','size','position','material','wall','outline','profile','rotation','holes','smooth']if k in p}for p in value['parts']]
 return value

def main():
 converter,validator=map(lambda p:str(Path(p).resolve()),sys.argv[1:])
 report=[]
 with tempfile.TemporaryDirectory()as folder:
  root=Path(folder)
  for limit in [6,4]:
   grammar=subprocess.run([converter],input=json.dumps(design_schema(limit)),text=True,capture_output=True,check=True)
   if grammar.stderr.strip():raise AssertionError(grammar.stderr)
   grammar_file=root/'workshop.gbnf';grammar_file.write_text(grammar.stdout)
   valid=ordered(RAW)
   cases=[('contour-hole-lathe',valid,True),('follow-up-question',{'questions':['Welche Maße soll dein Objekt haben?']},True)]
   for name,change in [('missing-parts',lambda r:r.pop('parts')),('missing-steps',lambda r:r.pop('steps')),('empty-parts',lambda r:r.update(parts=[])),('too-many-parts',lambda r:r.update(parts=r['parts']*5)),('unknown-code-field',lambda r:r['parts'][0].update(script='execute')),('unknown-shape',lambda r:r['parts'][0].update(shape='javascript')),('missing-outline',lambda r:r['parts'][0].pop('outline'))]:
    bad=copy.deepcopy(valid);change(bad);cases.append((name,bad,False))
   for name,value,expected in cases:
    data_file=root/'input.json';data_file.write_text(json.dumps(value,separators=(',',':')))
    result=subprocess.run([validator,str(grammar_file),str(data_file)],capture_output=True,text=True,check=True)
    accepted='Input string is valid according to the grammar.'in result.stdout
    if accepted!=expected:raise AssertionError(name+': '+result.stdout[:500]+result.stderr[:500])
    report.append(f'PASS limit={limit} {name}: '+('accepted'if accepted else'rejected'))
 print('\n'.join(report))
 print('Structural grammar only. Geometry validation and actual model quality require separate checks.')
if __name__=='__main__':main()
