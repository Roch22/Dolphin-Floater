import numpy as np, pickle, trimesh
from build_all import *
tt,ti=tube(sleeve_len=24, nrows=1); print('tube_test',ti)
st=sleeve(24, nrows=1)
c25,_=cap(0.25); c35,_=cap(0.35)
# socket test disc: same countersink + female thread as the dolphin, open on top
disc=cyl(22, 27) - revolve_profile([(25.5,-0.01),(28,-0.01),(28,3)]) - revolve_profile([(28,19),(28,22.01),(25.8,22.01)])
s=[cyl(COLLAR_CONE+0.01, COLLAR_R+0.35, TUBE_R+0.35, z0=-0.01), cyl(0.8, COLLAR_R+1.0, COLLAR_R+0.35, z0=-0.01),
   female_cutter(COLLAR_CONE-0.5, SOCK_THREAD+4, THREAD_CLR)]
disc=disc-mf.Manifold.batch_boolean(s, mf.OpType.Add)
# label on top face
from build_all import text_polys, shapely_to_manifold
lab=shapely_to_manifold(text_polys(["SOCKET"],3.2),0.61,z0=22-0.6)
lab=lab.translate((0,22.5,0))
disc=disc-lab
puck=cyl(20,25)-revolve_profile([(24.2,-0.01),(26,-0.01),(26,1.8)])-shapely_to_manifold(text_polys(["LEAK","TEST"],4.5),0.61,z0=19.4)
T={'tube_test':tt,'sleeve_test':st,'cap_0.25':c25,'cap_0.35':c35,'socket_test':disc,'leak_test_puck':puck}
for k,v in T.items():
    m=tm(v); print(k,m.is_watertight,round(m.volume/1000,1),m.bounds.round(1).tolist())
pickle.dump({k:(tm(v).vertices,tm(v).faces) for k,v in T.items()},open('tests.pkl','wb'))
# fit checks: test tube in socket disc, cap 0.35 on tube test (spin for best phase)
def flip(m): return m.rotate((180,0,0))
tub=flip(tt).translate((0,0,17.35))
print('socket disc vs tube_test overlap (cone seat facets only expected):', round((tub^disc).volume(),2))
