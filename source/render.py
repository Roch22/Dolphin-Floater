import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
def render(meshes, fn, views=((12,-70),(20,-130),(85,-90)), size=(16,6), lim=None, dpi=80):
    fig=plt.figure(figsize=size)
    allv=np.vstack([m.vertices for m,_ in meshes]); lo,hi=allv.min(0),allv.max(0)
    if lim is not None: lo,hi=lim
    c=(lo+hi)/2; r=(hi-lo).max()/2
    for i,(el,az) in enumerate(views):
        ax=fig.add_subplot(1,len(views),i+1,projection='3d')
        L=np.array([0.4,-0.6,0.7]); L/=np.linalg.norm(L)
        tris=np.vstack([m.vertices[m.faces] for m,_ in meshes])
        cols=np.vstack([np.clip(np.outer(0.35+0.65*np.clip(m.face_normals@L,0,1),col),0,1) for m,col in meshes])
        pc=Poly3DCollection(tris,edgecolor='none'); pc.set_facecolor(cols); ax.add_collection3d(pc)
        ax.set_xlim(c[0]-r,c[0]+r);ax.set_ylim(c[1]-r,c[1]+r);ax.set_zlim(c[2]-r,c[2]+r)
        ax.set_box_aspect((1,1,1)); ax.view_init(el,az); ax.axis('off')
    plt.subplots_adjust(0,0,1,1,0,0); plt.savefig(fn,dpi=dpi)
