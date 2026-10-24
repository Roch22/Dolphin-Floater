import pickle, trimesh, numpy as np
from render import render
A={k:trimesh.Trimesh(*v,process=False) for k,v in pickle.load(open('assembly.pkl','rb')).items()}
col=dict(dolphin=(0.40,0.60,0.92),tube=(0.78,0.78,0.80),sleeve=(0.20,0.36,0.75),cap=(0.20,0.36,0.75))
# assembled
render([(A[k],col[k]) for k in A],'preview_assembled.png',views=((5,-90),(15,-130),(15,-40)),size=(21,8),dpi=75)
# exploded
E=[]; off=dict(dolphin=0,tube=-25,sleeve=-55,cap=-90)
for k in A:
    m=A[k].copy(); m.apply_translation([0,0,off[k]]); E.append((m,col[k]))
render(E,'preview_exploded.png',views=((5,-90),),size=(8,10),dpi=75)
