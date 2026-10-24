"""Export every part in the release 3MFs as its own binary STL (one file per part).
Usage: python export_stl.py            -> writes an STL/ folder next to each release 3MF
Parts keep their print orientation (flat face on the bed) and are centred on x/y, z=0 on the bed."""
import glob, os, re, sys, zipfile
import xml.etree.ElementTree as ET
import numpy as np, trimesh

NS = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'releases')


def read_mesh(data):
    v, f = [], []
    for _, el in ET.iterparse(__import__('io').BytesIO(data)):
        if el.tag == NS + 'vertex':
            v.append((float(el.get('x')), float(el.get('y')), float(el.get('z'))))
        elif el.tag == NS + 'triangle':
            f.append((int(el.get('v1')), int(el.get('v2')), int(el.get('v3'))))
        el.clear()
    return trimesh.Trimesh(np.array(v), np.array(f), process=False)


def parts_in(path):
    """yield (part name, plate name, mesh) for each object in a 3MF written by threemf.py"""
    z = zipfile.ZipFile(path)
    cfg = z.read('Metadata/model_settings.config').decode()
    names = dict(re.findall(r'<object id="(\d+)">\s*<metadata key="name" value="([^"]+)"', cfg))
    plates = {}
    for pname, body in re.findall(r'<metadata key="plater_name" value="([^"]*)"/>(.*?)</plate>', cfg, re.S):
        for oid in re.findall(r'key="object_id" value="(\d+)"', body):
            plates[oid] = pname
    main = z.read('3D/3dmodel.model').decode()
    for comp_id, path_ in re.findall(r'<object id="(\d+)"[^>]*>\s*<components>\s*<component p:path="([^"]+)"', main):
        m = read_mesh(z.read(path_.lstrip('/')))
        yield names[comp_id], plates.get(comp_id, ''), m


def main(files):
    for path in files:
        out = os.path.join(os.path.dirname(path), 'STL')
        os.makedirs(out, exist_ok=True)
        print(os.path.relpath(path, ROOT))
        for i, (name, plate, m) in enumerate(parts_in(path)):
            b = m.bounds
            m.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
            fn = os.path.join(out, f'{name}.stl')
            m.export(fn)
            size = 'x'.join(f'{s:.0f}' for s in m.extents)
            print(f'  {name}.stl  plate "{plate}"  {size} mm  watertight={m.is_watertight}  {m.volume / 1000:.1f} cm3')


if __name__ == '__main__':
    main(sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, '*', '*.3mf'))))
