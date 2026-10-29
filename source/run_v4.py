import pickle, trimesh, numpy as np
from build_all import tm, to_mf, sleeve
from tube_v4 import tube4, rows4
T4,info=tube4(); T4t,_=tube4(sleeve_len=40, nrows=1)
P={k:to_mf(trimesh.Trimesh(*v,process=False)) for k,v in pickle.load(open('parts.pkl','rb')).items()}
old=P['tube']
for n,m in [('tube v3',old),('tube v4',T4),('tube_test v4',T4t)]:
    t=tm(m); print(n,'watertight',t.is_watertight,'vol %.1f cm3'%(t.volume/1000),'bounds',t.bounds.round(1).tolist())
print(info, rows4(info['zs0'],100))
# open area of one row (tube slot vs v3), and sleeve still closes: check overlap at 30 deg offset
S=sleeve(); 
def flip(m): return m.rotate((180,0,0))
tub=flip(T4).translate((0,0,17.35)); sl=flip(S).translate((0,0,17.35-20.5))
print('sleeve vs tube4 overlap', round((tub^sl).volume(),3))
# closed check: ray through tube slot centre at row middle, sleeve rotated 30 deg
import math
for off,name in [(0,'open'),(30,'closed'),(10,'2/3'),(20,'1/3')]:
    slr=sl.rotate((0,0,off)); both=tm(tub+slr)
    r=info['zs0']+9+11; z=17.35-r
    hits=0; N=0
    for a in np.linspace(-9,9,19):
        for dz in np.linspace(-9,9,7):
            o=[0,0,z+dz]; d=[math.cos(math.radians(a)),math.sin(math.radians(a)),0]
            N+=1; loc=both.ray.intersects_location([o],[d])[0]
            hits+= (len(loc)==0)
    print(name,'see-through %d%%'%(100*hits/N))
pickle.dump({'tube_v4':(tm(T4).vertices,tm(T4).faces),'tube_test_v4':(tm(T4t).vertices,tm(T4t).faces)},open('v4.pkl','wb'))
