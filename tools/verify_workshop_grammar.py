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
from tests.workshop_complex_fixture import ARM

def prepared(value):
 if isinstance(value,float):return round(value,5)
 if isinstance(value,list):return [prepared(v)for v in value]
 if isinstance(value,dict):return {k:prepared(v)for k,v in value.items()}
 return value

def ordered(value,complex_design=False):
 value=prepared(value)
 if 'parts'in value:
  value['parts']=[{k:p[k]for k in ['name','shape','size','position','material','wall','outline','profile','rotation','holes','smooth']if k in p}for p in value['parts']]
 if 'form'in value:value['form']={k:value['form'][k]for k in ['name','shape','size','position','material','wall','outline','profile','rotation','holes','smooth']if k in value['form']}
 if 'lighting'in value:value['lighting']={k:value['lighting'][k]for k in ['name','shape','size','position','material','wall','outline','profile','rotation','holes','smooth']if k in value['lighting']}
 keys=['form','lighting','title','parts','steps','features']+(['concept','explanation']if complex_design else['explanation','concept'])
 return {k:value[k]for k in keys if k in value}

def main():
 converter,validator=map(lambda p:str(Path(p).resolve()),sys.argv[1:])
 report=[]
 with tempfile.TemporaryDirectory()as folder:
  root=Path(folder)
  for limit,lighting,complex_design,example,form in [(6,None,False,RAW,None),(4,None,False,RAW,None),(6,True,False,RAW,None),(6,False,False,RAW,None),(10,True,True,ARM,None),(6,None,False,RAW,'round'),(6,None,False,RAW,'custom'),(6,True,False,RAW,'custom')]:
   grammar=subprocess.run([converter],input=json.dumps(design_schema(limit,lighting,complex_design,form=form)),text=True,capture_output=True,check=True)
   if grammar.stderr.strip():raise AssertionError(grammar.stderr)
   grammar_file=root/'workshop.gbnf';grammar_file.write_text(grammar.stdout)
   value=copy.deepcopy(example)
   if lighting is True:
    if complex_design:value['lighting']=value['parts'].pop(0)
    else:value['lighting']={'name':'LED-Modul','shape':'cylinder','size':[20,4,20],'position':[0,180,0],'material':'light'}
   if form:value['form']=value['parts'].pop(0)
   valid=ordered(value,complex_design)
   cases=[('contour-hole-lathe',valid,True),('follow-up-question',{'questions':['Welche Maße soll dein Objekt haben?']},True)]
   for name,change in [('missing-parts',lambda r:r.pop('parts')),('missing-steps',lambda r:r.pop('steps')),('too-many-parts',lambda r:r.update(parts=r['parts']*(limit+1))),('unknown-code-field',lambda r:r['parts'][0].update(script='execute')),('unknown-shape',lambda r:r['parts'][0].update(shape='javascript')),('missing-outline',lambda r:next(p for p in ([r['form']]if 'form'in r else[])+r['parts']if p['shape']=='extrude').pop('outline'))]:
    bad=copy.deepcopy(valid);change(bad);cases.append((name,bad,False))
   if form:
    for name,change in [('missing-form',lambda r:r.pop('form')),('box-form',lambda r:r['form'].update(shape='box')),('emitting-form',lambda r:r['form'].update(material='light'))]:
     bad=copy.deepcopy(valid);change(bad);cases.append((name,bad,False))
   if lighting is True:
    for name,change in [('missing-lighting',lambda r:r.pop('lighting')),('non-emitting-lighting',lambda r:r['lighting'].update(material='plastic'))]:
     bad=copy.deepcopy(valid);change(bad);cases.append((name,bad,False))
   if lighting is False:
    bad=copy.deepcopy(valid);bad['parts'][0]['material']='light';cases.append(('unwanted-light',bad,False))
   if complex_design:
    bad=copy.deepcopy(valid);bad.pop('concept');cases.append(('missing-complex-plan',bad,False))
   for name,value,expected in cases:
    data_file=root/'input.json';data_file.write_text(json.dumps(value,separators=(',',':')))
    result=subprocess.run([validator,str(grammar_file),str(data_file)],capture_output=True,text=True,check=True)
    accepted='Input string is valid according to the grammar.'in result.stdout
    if accepted!=expected:raise AssertionError(name+': '+result.stdout[:500]+result.stderr[:500])
    report.append(f'PASS limit={limit} LED={lighting} complex={complex_design} form={form} {name}: '+('accepted'if accepted else'rejected'))
 print('\n'.join(report))
 print('Structural grammar only. Geometry validation and actual model quality require separate checks.')
if __name__=='__main__':main()
