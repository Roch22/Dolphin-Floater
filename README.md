# Dolphin Tablet Floater

Hot tub tablet floater shaped like a dolphin. Designed by TheRock.
All parts print in PETG.

- Holds 8 tablets (25.2 x 16 mm).
- A turning sleeve opens or closes the slots, so you can set how fast the tablets dissolve.
- The screw-on cap has a sealed pocket for 1/2" stainless fender washers (pause at the first layer above 10 mm).
- The blowhole is the air vent, so the tube fills with water.

## What to print
Everything is in `releases/v3/`. Use the 3MF (3 plates, ready to slice) or the single-part STLs in `releases/v3/STL/`.

| Part | File | Size (mm) | Qty |
|---|---|---|---|
| Dolphin | `dolphin_float.stl` | 204 x 114 x 86 | 1 |
| Tube | `tube.stl` | 39 x 39 x 136 | 1 |
| Sleeve | `sleeve.stl` | 41 x 40 x 100 | 1 |
| Cap (pause for washers) | `cap_washer_pause.stl` | 46 x 46 x 30 | 1 |

Hardware: 4-5 stainless 1/2" fender washers (38 mm outside), dropped into the cap at the pause.
Slicer settings and the pause height are in `releases/v3/Print notes.txt`.
All STLs are already in print orientation (flat face down), so just drop them on the bed.

## Folders
- `releases/v3/`: latest full floater (one 3MF, 3 plates: dolphin, tube, sleeve + cap), `STL/` with one file per part, and print notes
- `releases/v1 test pack/`: test parts (thread caps, sleeve and tube test, socket test, leak puck), as a 3MF and in `STL/`
- `source/`: Python scripts that build every part (`run_main.py` for the parts, `run_tests.py` for the test pack, `export_stl.py` writes the `STL/` folders from the 3MFs)

## Version history
- **v1**: first version, plus the test pack
- **v2**: smooth dolphin body, plain base with no wave ripples
- **v3**: straight, smooth dorsal fin

## Test results
- Cap with 0.25 mm thread clearance: fits both ends of the tube
- Sleeve test: turns and locks
- Leak test puck: pending
