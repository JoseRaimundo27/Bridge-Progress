import open3d as o3d
import numpy as np

def get_grid_occupancy(pcd, plane, grid_size):
    """
    Projeta os pontos em um plano 2D específico e calcula quantas células do grid (S) são ocupadas.
    """
    points = np.asarray(pcd.points)
    
    if len(points) == 0:
        return 0
        
    # Seleciona os eixos para a projeção ortográfica
    if plane == 'xy':
        projected_points = points[:, [0, 1]]
    elif plane == 'xz':
        projected_points = points[:, [0, 2]]
    elif plane == 'yz':
        projected_points = points[:, [1, 2]]
    else:
        raise ValueError("Plano inválido. Escolha 'xy', 'xz' ou 'yz'.")
        
    # Discretização: divide pelas dimensões do grid e arredonda para achar o índice da célula
    grid_indices = np.floor(projected_points / grid_size).astype(int)
    
    # Remove duplicatas para contar apenas as células ocupadas (Superfície - S)
    unique_cells = np.unique(grid_indices, axis=0)
    
    return len(unique_cells)

def visualize_element_inspection(
    element_pcd,
    as_built_cloud,
    potential_points_pcd,
    expanded_bbox,
    show_full_cloud=False
):
    """
    Visualiza a seleção de pontos para inspeção do ACA.

    Cores:
      - Cinza: nuvem as-built completa (opcional)
      - Verde: elemento BIM (as-planned)
      - Vermelho: pontos as-built selecionados
      - Amarelo: bounding box expandida
    """

    geometries = []

    # Nuvem as-built completa, opcional
    if show_full_cloud:
        full_cloud = o3d.geometry.PointCloud(as_built_cloud)
        full_cloud.paint_uniform_color([0.65, 0.65, 0.65])
        geometries.append(full_cloud)

    # Elemento BIM planejado
    planned = o3d.geometry.PointCloud(element_pcd)
    planned.paint_uniform_color([0.0, 0.8, 0.2])
    geometries.append(planned)

    # Pontos selecionados pela bounding box
    selected = o3d.geometry.PointCloud(potential_points_pcd)
    selected.paint_uniform_color([1.0, 0.1, 0.1])
    geometries.append(selected)

    # Bounding box expandida
    box = o3d.geometry.AxisAlignedBoundingBox(
        expanded_bbox.get_min_bound(),
        expanded_bbox.get_max_bound()
    )
    box.color = [1.0, 0.8, 0.0]
    geometries.append(box)

    # Abre a janela de visualização
    o3d.visualization.draw_geometries(
        geometries,
        window_name="ACA - Inspecao dos pontos vizinhos",
        width=1280,
        height=800,
        point_show_normal=False
    )

def evaluate_element_status(as_planned_path, as_built_cloud, element_type, d_avg, c_buffer, grid_size=0.05):
    """
    Executa o Módulo III para um único elemento as-planned em .ply.
    element_type: 'horizontal' (laje/teto), 'vertical' (parede/pilar), 'unclear' (vigas)
    grid_size: Resolução do grid em metros (ex: 0.05 = 5cm)
    """
    # 1. Carregar o elemento planejado (BIM extraído em .ply)
    element_pcd = o3d.io.read_point_cloud(as_planned_path)
    
    # 2. Busca de Pontos Vizinhos (Adaptive Parameter O_thr)
    o_thr = d_avg + c_buffer
    
    # Criar e expandir a bounding box
    bbox = element_pcd.get_axis_aligned_bounding_box()
    min_bound = bbox.get_min_bound() - o_thr
    max_bound = bbox.get_max_bound() + o_thr
    expanded_bbox = o3d.geometry.AxisAlignedBoundingBox(min_bound, max_bound)
    
    # Cortar a nuvem as-built para isolar os 'Potential point sets'
    potential_points_pcd = as_built_cloud.crop(expanded_bbox)

    print("Pontos no elemento BIM:", len(element_pcd.points))
    print("Pontos vizinhos:", len(potential_points_pcd.points))

    print("\nDimensões da bounding box original:")
    print(bbox.get_extent())

    print("\nDimensões da bounding box expandida:")
    print(expanded_bbox.get_extent())

    
    # 3. Cálculo das áreas de projeção (SP = as-built cortado, SE = as-planned)
    # Plano XY
    sp_xy = get_grid_occupancy(potential_points_pcd, 'xy', grid_size)
    se_xy = get_grid_occupancy(element_pcd, 'xy', grid_size)
    
    # Plano XZ
    sp_xz = get_grid_occupancy(potential_points_pcd, 'xz', grid_size)
    se_xz = get_grid_occupancy(element_pcd, 'xz', grid_size)
    
    # Plano YZ
    sp_yz = get_grid_occupancy(potential_points_pcd, 'yz', grid_size)
    se_yz = get_grid_occupancy(element_pcd, 'yz', grid_size)

    
    
    # 4. Cálculo do CAI com base na Pose do Elemento
    cai = 0.0
    
    try:
        if element_type == 'horizontal':
            # Coverage 1 (Lajes e Tetos)
            cai = sp_xy / se_xy if se_xy > 0 else 0
            
        elif element_type == 'vertical':
            # Coverage 2 (Paredes e Colunas)
            cai = (sp_xz + sp_yz) / (se_xz + se_yz) if (se_xz + se_yz) > 0 else 0
            
        elif element_type == 'unclear':
            # Coverage 3 (Vigas)
            cai = (sp_xy + sp_xz + sp_yz) / (se_xy + se_xz + se_yz) if (se_xy + se_xz + se_yz) > 0 else 0
            
    except ZeroDivisionError:
        cai = 0.0

    print(f"D_avg: {d_avg}")
    print(f"C_buffer: {c_buffer}")
    print(f"O_thr: {o_thr}")

    print("\n=== Células ocupadas por projeção ===")
    print(f"XY | SP: {sp_xy:>5} | SE: {se_xy:>5}")
    print(f"XZ | SP: {sp_xz:>5} | SE: {se_xz:>5}")
    print(f"YZ | SP: {sp_yz:>5} | SE: {se_yz:>5}")

    print(f"CAI: {cai}")
    print(f"Quantidade de pontos vizinhos: {len(potential_points_pcd.points)}")    

    # 5. Avaliação do Status (Threshold = 0.5)
    status = "Existent" if cai > 0.5 else "Non-existent"

    visualize_element_inspection(
    element_pcd=element_pcd,
    as_built_cloud=as_built_cloud,
    potential_points_pcd=potential_points_pcd,
    expanded_bbox=expanded_bbox,
    show_full_cloud=False
    )
    
    return {
        "status": status,
        "cai": round(cai, 3),
        "potential_points_count": len(potential_points_pcd.points)
    }

# ==========================================
# Exemplo de Uso
# ==========================================
if __name__ == "__main__":
    # Carregue sua nuvem as-built completa 
     as_built_cloud = o3d.io.read_point_cloud("../AsBuilt/D19/asbuilt_registered.ply")
    
    # Definir parâmetros (ajuste de acordo com a qualidade do seu registro e tolerância construtiva)
     D_avg_exemplo = 0.5745
     C_buffer_exemplo = 0.15 # 10 cm de buffer empírico
    
    # Rodar a avaliação para uma parede (elemento vertical)
     result = evaluate_element_status(
        as_planned_path="../AsPlanned/Geometry/pilar1/1cU0CVJVrE7f42i83xxTnA.ply",
        #as_planned_path="../AsPlanned/Geometry/pilar2/1cU0CVJVrE7f42i83xxTnR.ply",
         #as_planned_path="../AsPlanned/Geometry/pilar3/1cU0CVJVrE7f42i83xxTne.ply",
         #as_planned_path="../AsPlanned/Geometry/pilar4/1cU0CVJVrE7f42i83xxTnv.ply",
        #as_planned_path="../AsPlanned/Geometry/pilar5/1cU0CVJVrE7f42i83xxTmX.ply",
         #as_planned_path="../AsPlanned/Geometry/pilar6/1cU0CVJVrE7f42i83xxTms.ply",
         #as_planned_path="../AsPlanned/Geometry/pilar8/1cU0CVJVrE7f42i83xxTtX.ply",
        # as_planned_path="../AsPlanned/Geometry/pilar9/1cU0CVJVrE7f42i83xxTts.ply",


         as_built_cloud=as_built_cloud,
         element_type="vertical",
         d_avg=D_avg_exemplo,
         c_buffer=C_buffer_exemplo,
         grid_size=0.05 # grid de 5x5 cm para a projeção
     )
     print(result)