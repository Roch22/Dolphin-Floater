import numpy as np, pickle, trimesh, time
from build_all import *
t=time.time()
body=dolphin_body(0.55); print('body',time.time()-t)
SOCK=(6.0,0.0); VENT=(44.0,0.0,64.0)
D,dinfo=dolphin(SOCK,VENT,body=body)
T,tinfo=tube(); S=sleeve(); C,cinfo=cap()
parts=dict(dolphin=D,tube=T,sleeve=S,cap=C)
for k,v in parts.items():
    m=tm(v); print(k,'watertight',m.is_watertight,'vol',round(m.volume/1000,1),'bounds',m.bounds.round(1).tolist())
pickle.dump({k:(tm(v).vertices,tm(v).faces) for k,v in parts.items()},open('parts.pkl','wb'))
H=cinfo['H']
def flip(m): return m.rotate((180,0,0))
x0=SOCK[0]
A=dict(dolphin=D,tube=flip(T).translate((x0,0,17.35)),sleeve=flip(S).translate((x0,0,17.35-20.5)),
       cap=C.translate((x0,0,-H-103.15)))
pickle.dump({k:(tm(v).vertices,tm(v).faces) for k,v in A.items()},open('assembly.pkl','wb'))
for a,b in [('dolphin','sleeve'),('sleeve','tube'),('cap','sleeve'),('cap','dolphin')]:
    print('overlap',a,b,round((A[a]^A[b]).volume(),3))
rho=1.27; Dm=tm(D); shell=Dm.area*1.2; dol=rho*(shell+0.10*(Dm.volume-shell))/1000
tm_,sm,cm=[rho*A[k].volume()/1000 for k in ('tube','sleeve','cap')]
fixed=(A['tube'].volume()+A['sleeve'].volume()+A['cap'].volume())/1000
tab_v=8*np.pi*1.26**2*1.6
print('masses g dolphin %.0f tube %.0f sleeve %.0f cap %.0f'%(dol,tm_,sm,cm))
def wl(M,V):
    lo,hi=0,82
    for _ in range(35):
        z=(lo+hi)/2; sub=D.trim_by_plane((0,0,-1),-z).volume()/1000
        lo,hi=(z,hi) if sub+fixed+V<M else (lo,z)
    return z
base=dol+tm_+sm+cm
for n,M,V in [('8 tablets(16g) + 4 washers',base+52+tab_v*2,6.6+tab_v),('8 tablets(20g) + 4 washers',base+52+160,6.6+tab_v),
              ('8 tablets, no washers',base+tab_v*2,tab_v),('empty + 4 washers',base+52,6.6)]:
    print(n,'total %.0f g -> waterline %.1f mm up the dolphin'%(M,wl(M,V)))
pickle.dump(dict(SOCK=SOCK,VENT=VENT,H=H,dol=dol),open('info.pkl','wb'))
