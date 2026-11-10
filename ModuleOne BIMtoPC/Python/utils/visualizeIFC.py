import ifcopenshell
import ifcopenshell.geom
import open3d as o3d
import numpy as np

# Caminho do arquivo IFC
ifc_path = "../Modelos/RSP-116RJ-218-226-ACA-EXE-MB-L2-007-R01-2x3.ifc"

# Abrir IFC
ifc = ifcopenshell.open(ifc_path)

# Configurações da geometria
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)

meshes = []

# Percorre todos os produtos geométricos
for product in ifc.by_type("IfcProduct"):

    # Ignora elementos sem representação geométrica
    if not product.Representation:
        continue

    try:
        # Gera geometria
        shape = ifcopenshell.geom.create_shape(settings, product)
        geometry = shape.geometry

        # Vértices
        verts = np.array(geometry.verts).reshape(-1, 3)

        # Faces triangulares
        faces = np.array(geometry.faces).reshape(-1, 3)

        # Cria malha Open3D
        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(verts)
        mesh.triangles = o3d.utility.Vector3iVector(faces)

        mesh.compute_vertex_normals()

        meshes.append(mesh)

    except Exception as e:
        print(f"Erro em {product.GlobalId}: {e}")

# Junta todas as malhas
if len(meshes) > 0:
    full_mesh = meshes[0]

    for m in meshes[1:]:
        full_mesh += m

    full_mesh.compute_vertex_normals()

    # Visualização
    o3d.visualization.draw_geometries(
        [full_mesh],
        window_name="Visualizador IFC",
        width=1200,
        height=800,
        mesh_show_back_face=True
    )

else:
    print("Nenhuma geometria encontrada.")