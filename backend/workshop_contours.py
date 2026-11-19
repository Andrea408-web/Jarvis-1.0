"""Small, validated 2D contours for real extrusions/cutouts and lathe profiles."""
import math

def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def on(a,b,p):return abs(cross(a,b,p))<1e-9 and min(a[0],b[0])-1e-9<=p[0]<=max(a[0],b[0])+1e-9 and min(a[1],b[1])-1e-9<=p[1]<=max(a[1],b[1])+1e-9
def intersects(a,b,c,d):
 x,y,z,w=cross(a,b,c),cross(a,b,d),cross(c,d,a),cross(c,d,b)
 return x*y<0 and z*w<0 or on(a,b,c)or on(a,b,d)or on(c,d,a)or on(c,d,b)
def points(value,cap=96):
 if not isinstance(value,list)or not 3<=len(value)<=cap:raise ValueError('Konturen brauchen 3 bis '+str(cap)+' Punkte.')
 if any(not isinstance(p,list)or len(p)!=2 or any(type(n)not in {int,float}or not math.isfinite(n)or abs(n)>.500001 for n in p)for p in value):raise ValueError('Ungültige Konturkoordinaten.')
 result=[list(p)for p in value]
 if result[0]==result[-1]:result.pop()
 if len(result)<3:raise ValueError('Die Kontur hat zu wenige verschiedene Punkte.')
 edges=list(zip(result,result[1:]+result[:1]))
 if any(a==b for a,b in edges):raise ValueError('Doppelte Konturpunkte.')
 area=sum(a[0]*b[1]-b[0]*a[1]for a,b in edges)/2
 if abs(area)<1e-5:raise ValueError('Die Kontur hat keine ausreichende Fläche.')
 for i,(a,b)in enumerate(edges):
  for j,(c,d)in enumerate(edges):
   if j<=i+1 or i==0 and j==len(edges)-1:continue
   if intersects(a,b,c,d):raise ValueError('Die Kontur überschneidet sich selbst.')
 return result

def inside(p,poly):
 result=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if on(a,b,p):return False
  if (a[1]>p[1])!=(b[1]>p[1])and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:result=not result
 return result

def smooth_closed(poly):
 result=[];count=min(96,len(poly)*4)
 for i in range(count):
  t=i*len(poly)/count;j=int(t);u=t-j;a,b,c,d=[poly[k%len(poly)]for k in [j-1,j,j+1,j+2]]
  result.append([.5*((2*b[k])+(-a[k]+c[k])*u+(2*a[k]-5*b[k]+4*c[k]-d[k])*u*u+(-a[k]+3*b[k]-3*c[k]+d[k])*u*u*u)for k in range(2)])
 return result

def contour(part):
 outer=points(part.get('outline'));holes=part.get('holes',[])
 if not isinstance(holes,list)or len(holes)>8:raise ValueError('Maximal acht Ausschnitte je Kontur.')
 checked=[points(h,48)for h in holes]
 if type(part.get('smooth',False))is not bool:raise ValueError('Ungültiger Kurvenschalter.')
 if part.get('smooth'):
  outer=smooth_closed(outer);low=[min(p[k]for p in outer)for k in range(2)];high=[max(p[k]for p in outer)for k in range(2)]
  if any(high[k]-low[k]<.01 for k in range(2)):raise ValueError('Die Kurve ist zu schmal.')
  def fit(poly):return [[(p[k]-low[k])/(high[k]-low[k])-.5 for k in range(2)]for p in poly]
  outer=points(fit(outer));checked=[points(fit(h),48)for h in checked]
 for i,hole in enumerate(checked):
  if not all(inside(p,outer)for p in hole):raise ValueError('Ein Ausschnitt liegt außerhalb der Kontur.')
  for a,b in zip(hole,hole[1:]+hole[:1]):
   for c,d in zip(outer,outer[1:]+outer[:1]):
    if intersects(a,b,c,d):raise ValueError('Ein Ausschnitt schneidet den Außenrand.')
  for old in checked[:i]:
   if inside(hole[0],old)or inside(old[0],hole):raise ValueError('Verschachtelte Ausschnitte sind nicht erlaubt.')
   if any(intersects(a,b,c,d)for a,b in zip(hole,hole[1:]+hole[:1])for c,d in zip(old,old[1:]+old[:1])):raise ValueError('Ausschnitte überschneiden sich.')
 lo=[min(p[k]for p in outer)for k in range(2)];hi=[max(p[k]for p in outer)for k in range(2)]
 if any(hi[k]-lo[k]<.01 for k in range(2)):raise ValueError('Die Kontur ist zu schmal.')
 def normalize(poly):return [[(p[k]-lo[k])/(hi[k]-lo[k])-.5 for k in range(2)]for p in poly]
 return normalize(outer),[normalize(h)for h in checked]

def profile(value):
 if not isinstance(value,list)or not 3<=len(value)<=64:raise ValueError('Ein Drehprofil braucht 3 bis 64 Punkte.')
 if any(not isinstance(p,list)or len(p)!=2 or any(type(n)not in {int,float}or not math.isfinite(n)for n in p)or not 0<=p[0]<=.5 or not -.5<=p[1]<=.5 for p in value):raise ValueError('Ungültiges Drehprofil.')
 if any(value[i+1][1]<p[1]for i,p in enumerate(value[:-1])):raise ValueError('Das Drehprofil muss von unten nach oben verlaufen.')
 radius=max(p[0]for p in value);lo=min(p[1]for p in value);hi=max(p[1]for p in value)
 if radius<.01 or hi-lo<.01:raise ValueError('Das Drehprofil hat keine ausreichende Ausdehnung.')
 return [[p[0]/radius*.5,(p[1]-lo)/(hi-lo)-.5]for p in value]
