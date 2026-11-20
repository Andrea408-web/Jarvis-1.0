"""Constrained output contract shared by the two supported local runtimes.

The schema constrains syntax/fields; workshop_free still checks geometry and intent.
No geometry or object template is substituted if inference fails.
"""
import copy

def text(cap):return {'type':'string','minLength':1,'maxLength':cap}
def array(items,minimum,maximum):return {'type':'array','items':items,'minItems':minimum,'maxItems':maximum}
def obj(properties,required=None):return {'type':'object','properties':properties,'required':list(properties)if required is None else required,'additionalProperties':False}
def number(lo,hi):return {'type':'number','minimum':lo,'maximum':hi}

def design_schema(part_limit=6):
    vector=array(number(-1200,1200),3,3)
    point=array(number(-.5,.5),2,2)
    outline=array(point,3,24)
    common={'name':text(80),'shape':{'enum':['box','cylinder','sphere','torus','tube','shade','extrude','lathe']},'size':array(number(.1,1200),3,3),'position':vector,'material':{'enum':['wood','metal','plastic','diffuser','light']},'rotation':array(number(-180,180),3,3)}
    required=['name','shape','size','position','material']
    variants=[]
    for shapes,extra in [(['box','cylinder','sphere','torus','shade'],{}),(['tube'],{'wall':number(.1,599)}),(['extrude'],{'outline':outline}),(['lathe'],{'profile':array({'type':'array','prefixItems':[number(0,.5),number(-.5,.5)],'minItems':2,'maxItems':2},3,16)})]:
        properties={**copy.deepcopy(common),'shape':{'enum':shapes},**copy.deepcopy(extra)}
        if shapes==['extrude']:properties.update(holes=array(outline,0,4),smooth={'type':'boolean'})
        variants.append(obj(properties,required+list(extra)))
    design=obj({'title':text(90),'parts':array({'anyOf':variants},1,part_limit),'steps':array(text(300),1,6),'features':array(text(240),1,4),'explanation':text(700)},['title','parts','steps','features'])
    questions=obj({'questions':array(text(240),1,3)})
    return {'anyOf':[design,questions]}
