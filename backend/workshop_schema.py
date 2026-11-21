"""Constrained output contract shared by the two supported local runtimes.

The schema constrains syntax/fields; workshop_free still checks geometry and intent.
No geometry or object template is substituted if inference fails.
"""
import copy

def text(cap):return {'type':'string','minLength':1,'maxLength':cap}
def array(items,minimum,maximum):return {'type':'array','items':items,'minItems':minimum,'maxItems':maximum}
def obj(properties,required=None):return {'type':'object','properties':properties,'required':list(properties)if required is None else required,'additionalProperties':False}
def number(lo,hi):return {'type':'number','minimum':lo,'maximum':hi}

def design_schema(part_limit=6,lighting=None,complex_design=False,form=None):
    vector=array(number(-1200,1200),3,3)
    point=array(number(-.5,.5),2,2)
    outline=array(point,3,24)
    common={'name':text(80),'shape':{'enum':['box','cylinder','sphere','torus','tube','shade','extrude','lathe']},'size':array(number(.1,1200),3,3),'position':vector,'material':{'enum':['wood','metal','plastic','diffuser']+([]if lighting is False else['light'])},'rotation':array(number(-180,180),3,3)}
    required=['name','shape','size','position','material']
    variants=[]
    for shapes,extra in [(['box','cylinder','sphere','torus','shade'],{}),(['tube'],{'wall':number(.1,599)}),(['extrude'],{'outline':outline}),(['lathe'],{'profile':array({'type':'array','prefixItems':[number(0,.5),number(-.5,.5)],'minItems':2,'maxItems':2},3,16)})]:
        properties={**copy.deepcopy(common),'shape':{'enum':shapes},**copy.deepcopy(extra)}
        if shapes==['extrude']:properties.update(holes=array(outline,0,4),smooth={'type':'boolean'})
        variants.append(obj(properties,required+list(extra)))
    reserved=int(lighting is True)+int(bool(form))
    parts=array({'anyOf':variants},0 if reserved else 1,max(0,part_limit-reserved))
    properties={}
    if form:
        forms=copy.deepcopy(variants)
        for variant in forms:variant['properties']['material']={'enum':['wood','metal','plastic','diffuser']}
        forms=[v for v in forms if any(shape!='box' and (form!='custom' or shape in {'extrude','lathe'})for shape in v['properties']['shape']['enum'])]
        for variant in forms:variant['properties']['shape']['enum']=[shape for shape in variant['properties']['shape']['enum']if shape!='box']
        if form=='custom':
            for variant in forms:
                if 'outline'in variant['properties']:variant['properties']['outline']['minItems']=5
                if 'profile'in variant['properties']:variant['properties']['profile']['minItems']=4
        properties['form']={'anyOf':forms}
    if lighting is True:
        emitters=copy.deepcopy(variants)
        for variant in emitters:variant['properties']['material']={'const':'light'}
        properties['lighting']={'anyOf':emitters}
    concept=obj({'systems':array(obj({'name':text(80),'function':text(260)}),2,6),'workflow':array(text(300),1,6),'unresolved':array(text(300),1,6)})
    design=obj({**properties,'title':text(90),'parts':parts,'steps':array(text(300),1,6),'features':array(text(240),1,4),'explanation':text(700),'concept':concept},(['form']if form else[])+(['lighting']if lighting is True else[])+['title','parts','steps','features']+(['concept']if complex_design else[]))
    questions=obj({'questions':array(text(240),1,3)})
    return {'anyOf':[design,questions]}
