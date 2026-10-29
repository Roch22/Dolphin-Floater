import pickle, trimesh, os, shutil
import threemf
from render import render
P={k:trimesh.Trimesh(*v,process=False) for k,v in pickle.load(open('parts.pkl','rb')).items()}
V={k:trimesh.Trimesh(*v,process=False) for k,v in pickle.load(open('v4.pkl','rb')).items()}
old=P['tube'].copy(); old.apply_translation([-45,0,0]); new=V['tube_v4'].copy(); new.apply_translation([45,0,0])
render([(old,(0.75,0.5,0.2)),(new,(0.95,0.55,0.15))],'tube_v3_vs_v4.png',views=((8,-90),),size=(9,9),dpi=80)
out='Dolphin Floater v4'; shutil.rmtree(out,ignore_errors=True); os.makedirs(out)
C=128
threemf.write(f'{out}/Dolphin Floater v4.3mf',[
  ('Dolphin',[('dolphin_float',P['dolphin'],(C,C))]),
  ('Tube (stronger)',[('tube_v4',V['tube_v4'],(C,C))]),
  ('Sleeve + Cap',[('sleeve',P['sleeve'],(C-40,C)),('cap_washer_pause',P['cap'],(C+40,C))])])
threemf.write(f'{out}/Tube v4 test.3mf',[('Tube test v4',[('tube_test_v4',V['tube_test_v4'],(C,C))])])
shutil.copy('tube_v3_vs_v4.png',f'{out}/tube v3 vs v4.png')
open(f'{out}/Print notes v4.txt','w').write('''DOLPHIN FLOATER v4 - STRONGER TUBE
==================================
WHAT CHANGED (tube only)
  - Slots narrower (18 deg instead of 26 deg), so the 6 ribs between them are 12 mm wide instead of 10 mm
  - Solid bands at both ends 9 mm instead of 5 mm, and 7 mm instead of 4.5 mm between the rows
  - Slot ends taper to a point: no sharp corners for a crack to start, no bridges to print
  - Wall a bit thicker (bore 26.6 mm instead of 27.2 mm, still fits 25.2 mm tablets)
  - About 28% more plastic in the tube
  - Same threads and collar: your cap, sleeve and the dolphin socket still fit

SLEEVE SETTINGS WITH THE v4 TUBE (same sleeve, same ticks)
  long tick   = fully open
  1st short   = about 2/3 open
  2nd short   = nearly closed (about 10%)
  medium tick = closed

PRINT SETTINGS FOR THE TUBE (strength)
  PETG, not PLA (PLA is brittle, and softens and weakens in hot tub water)
  Wall loops 6
  Sparse infill density 100%
  Top shell layers 5, Bottom shell layers 5
  Stand it up as loaded. No supports.
  Optional: Nozzle temperature +5 C (e.g. 240 C) for stronger layer bonding

WHEN SCREWING
  Hold the tube by the collar or the solid band next to the thread you are turning,
  not by the slotted middle. Hand tight is enough.

FILES
  Dolphin Floater v4.3mf : dolphin (v3), tube v4, sleeve + cap
  Tube v4 test.3mf        : short tube (one slot row, both threads) to try first
''')
print(os.listdir(out))
