"""Minimal Bambu/Orca-style multi-plate 3MF writer (one object per mesh, plates by list)."""
import zipfile, uuid, numpy as np

BED = 256.0          # Creator 5 Pro bed
GAP = 1.0 / 5.0      # Orca LOGICAL_PART_PLATE_GAP


def _cols(n):
    v = np.sqrt(n); r = round(v)
    return int(r + 1 if v > r else r)


def plate_origin(i, n):
    c = _cols(n)
    return (i % c) * BED * (1 + GAP), -(i // c) * BED * (1 + GAP)


def mesh_xml(oid, name, tm):
    v = "\n".join(f'     <vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in tm.vertices)
    t = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tm.faces)
    return (f'  <object id="{oid}" p:UUID="{uuid.uuid4()}" type="model">\n   <mesh>\n    <vertices>\n{v}\n'
            f'    </vertices>\n    <triangles>\n{t}\n    </triangles>\n   </mesh>\n  </object>\n')


def write(path, plates):
    """plates: list of (plate_name, [(obj_name, trimesh, (x,y) bed position of bbox centre), ...])"""
    n = len(plates)
    sub_objs, main_objs, items, cfg_objs, cfg_plates = [], [], [], [], []
    oid = 1
    for pi, (pname, objs) in enumerate(plates):
        ox, oy = plate_origin(pi, n)
        inst = []
        for (name, tm, (bx, by)) in objs:
            m = tm.copy()
            b = m.bounds
            m.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
            mesh_id, comp_id = oid, oid + 1; oid += 2
            sub_objs.append(mesh_xml(mesh_id, name, m))
            main_objs.append(
                f'  <object id="{comp_id}" p:UUID="{uuid.uuid4()}" type="model">\n   <components>\n'
                f'    <component p:path="/3D/Objects/object_{mesh_id}.model" objectid="{mesh_id}" '
                f'p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n   </components>\n  </object>\n')
            tx, ty = ox + bx, oy + by
            items.append(f'  <item objectid="{comp_id}" p:UUID="{uuid.uuid4()}" '
                         f'transform="1 0 0 0 1 0 0 0 1 {tx:.3f} {ty:.3f} 0" printable="1"/>\n')
            cfg_objs.append(
                f'  <object id="{comp_id}">\n    <metadata key="name" value="{name}"/>\n'
                f'    <metadata key="extruder" value="1"/>\n'
                f'    <part id="{mesh_id}" subtype="normal_part">\n      <metadata key="name" value="{name}"/>\n'
                f'      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                f'      <metadata key="extruder" value="1"/>\n    </part>\n  </object>\n')
            inst.append(f'    <model_instance>\n      <metadata key="object_id" value="{comp_id}"/>\n'
                        f'      <metadata key="instance_id" value="0"/>\n'
                        f'      <metadata key="identify_id" value="{100 + comp_id}"/>\n    </model_instance>\n')
        cfg_plates.append(f'  <plate>\n    <metadata key="plater_id" value="{pi + 1}"/>\n'
                          f'    <metadata key="plater_name" value="{pname}"/>\n'
                          f'    <metadata key="locked" value="false"/>\n' + "".join(inst) + '  </plate>\n')
    NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
          'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')
    main = (f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS}>\n'
            ' <metadata name="Application">BambuStudio-01.10.02.76</metadata>\n'
            ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
            ' <metadata name="Title">Dolphin tablet floater</metadata>\n'
            ' <metadata name="Designer">TheRock</metadata>\n'
            ' <resources>\n' + "".join(main_objs) + ' </resources>\n'
            f' <build p:UUID="{uuid.uuid4()}">\n' + "".join(items) + ' </build>\n</model>\n')
    rels_main = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                 ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
                 '</Relationships>\n')
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
          ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
          ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
          ' <Default Extension="config" ContentType="text/xml"/>\n</Types>\n')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('_rels/.rels', rels_main)
        z.writestr('3D/3dmodel.model', main)
        rel_lines = []
        for k, so in enumerate(sub_objs):
            mid = int(so.split('id="')[1].split('"')[0])
            z.writestr(f'3D/Objects/object_{mid}.model',
                       f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS}>\n'
                       ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n' + so +
                       ' </resources>\n <build/>\n</model>\n')
            rel_lines.append(f' <Relationship Target="/3D/Objects/object_{mid}.model" Id="rel-{k + 1}" '
                             'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n')
        z.writestr('3D/_rels/3dmodel.model.rels',
                   '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                   + "".join(rel_lines) + '</Relationships>\n')
        z.writestr('Metadata/model_settings.config',
                   '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "".join(cfg_objs) + "".join(cfg_plates) + '</config>\n')
