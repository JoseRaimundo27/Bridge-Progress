import open3d as o3d

# Carrega a nuvem em UTM
pcd = o3d.io.read_point_cloud("../Modelos/s07_utm_asplanned.ply")

# Subtrai o centroide para transformar em coordenadas locais com centro em (0,0,0)
pcd.translate(-pcd.get_center())

# Salva a nova nuvem local
o3d.io.write_point_cloud("../Modelos/s07_local_asplanned.ply", pcd)

print("Nuvem convertida para coordenadas locais com sucesso!")