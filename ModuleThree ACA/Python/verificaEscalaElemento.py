
import open3d as o3d
import numpy as np

# 1. Carregar a nuvem de pontos
pcd = o3d.io.read_point_cloud(
    "../AsPlanned/Geometry/pilar5/1cU0CVJVrE7f42i83xxTmX.ply"
)

# Verificar se a nuvem foi carregada
if pcd.is_empty():
    raise ValueError("A nuvem de pontos está vazia ou não foi carregada.")

# 2. Calcular a bounding box alinhada aos eixos
aabb = pcd.get_axis_aligned_bounding_box()

# 3. Definir cores
pcd.paint_uniform_color([0.7, 0.7, 0.7])  # Cinza
aabb.color = (1, 0, 0)                    # Vermelho

# 4. Obter dimensões
min_pt = aabb.get_min_bound()
max_pt = aabb.get_max_bound()
dimensoes = max_pt - min_pt

print(f"Limites mínimos (X, Y, Z): {min_pt}")
print(f"Limites máximos (X, Y, Z): {max_pt}")
print(f"Dimensões (X, Y, Z): {dimensoes}")

# 5. Visualizar nuvem + bounding box
o3d.visualization.draw_geometries(
    [pcd, aabb],
    window_name="Pilar 5 - Bounding Box AABB",
    width=1200,
    height=800,
    mesh_show_wireframe=True
)
