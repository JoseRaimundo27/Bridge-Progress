import open3d as o3d
import numpy as np
import copy
import math

def get_2d_main_axes(pcd):
    """
    Calcula a OBB (Oriented Bounding Box) e extrai os eixos longos e curtos 
    projetados no plano XY.
    """
    obb = pcd.get_oriented_bounding_box()
    extents = obb.extent
    R = obb.R
    
    # Focando no plano XY (assumindo eixo Z como vertical)
    axis_0 = R[:, 0][:2]
    axis_1 = R[:, 1][:2]
    
    length_0, length_1 = extents[0], extents[1]
    
    if length_0 >= length_1:
        return (axis_0, length_0), (axis_1, length_1) # Long, Short
    else:
        return (axis_1, length_1), (axis_0, length_0) # Long, Short

def rotation_matrix_2d_to_4x4(v_source, v_target):
    """
    Calcula a matriz 4x4 (rotação no eixo Z) necessária para alinhar v_source com v_target.
    """
    v_s = v_source / np.linalg.norm(v_source)
    v_t = v_target / np.linalg.norm(v_target)
    
    angle = math.atan2(v_t[1], v_t[0]) - math.atan2(v_s[1], v_s[0])
    
    R = np.eye(4)
    R[0, 0] = math.cos(angle)
    R[0, 1] = -math.sin(angle)
    R[1, 0] = math.sin(angle)
    R[1, 1] = math.cos(angle)
    return R

def obbp_icp(scan_raw, bim_raw, voxel_size=0.1, square_tol=0.15, icp_dist_thresh=0.5):
    """
    Implementação do Algoritmo 1: OBBP-ICP
    """
    # Step 1: Preprocessing
    scan_down = scan_raw.voxel_down_sample(voxel_size)
    bim_down = bim_raw.voxel_down_sample(voxel_size)
    
    scan_center = scan_down.get_center()
    bim_center = bim_down.get_center()
    
    T_align = np.eye(4)
    T_align[:3, 3] = bim_center - scan_center
    scan_trans = copy.deepcopy(scan_down).transform(T_align)
    
    R_z = np.eye(4)
    scan_z = copy.deepcopy(scan_trans).transform(R_z)
    
    # Step 2: Bounding Box Alignment
    (axis_scan_long, _), (axis_scan_short, _) = get_2d_main_axes(scan_z)
    (axis_bim_long, ext_bim_l), (axis_bim_short, ext_bim_s) = get_2d_main_axes(bim_down)
    
    candidates = []
    is_square = abs(ext_bim_l - ext_bim_s) / max(ext_bim_l, ext_bim_s) <= square_tol
    
    if is_square: # 4 Candidates
        align_targets = [axis_bim_long, axis_bim_short, -axis_bim_long, -axis_bim_short]
    else: # Non-Square: 2 Candidates
        align_targets = [axis_bim_long, -axis_bim_long]
        
    for target_vector in align_targets:
        R_align_i = rotation_matrix_2d_to_4x4(axis_scan_long, target_vector)
        scan_cand_i = copy.deepcopy(scan_z).transform(R_align_i)
        candidates.append((R_align_i, scan_cand_i))

    # Step 3 & 4: Refinement with ICP & Select Best Alignment
    best_fitness = -1.0
    R_best = np.eye(4)
    M_icp_best = np.eye(4)
    
    criteria = o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=50)
    
    for R_align_i, scan_cand_i in candidates:
        icp_result = o3d.pipelines.registration.registration_icp(
            scan_cand_i, bim_down, icp_dist_thresh, np.eye(4),
            o3d.pipelines.registration.TransformationEstimationPointToPoint(),
            criteria
        )
        
        if icp_result.fitness > best_fitness:
            best_fitness = icp_result.fitness
            R_best = R_align_i
            M_icp_best = icp_result.transformation
            
    # M_total = M_icp * R_best * R_z * T_align
    M_total = M_icp_best @ R_best @ R_z @ T_align

    # Step 5: Final Transformation and Output
    scan_regis = copy.deepcopy(scan_raw).transform(M_total)
    
    distances = scan_regis.compute_point_cloud_distance(bim_raw)
    d_avg = np.mean(distances) if len(distances) > 0 else float('inf')
    
    return scan_regis, d_avg, M_total

def obbp_icp_corrigido(scan_raw, bim_raw, voxel_size=0.1, square_tol=0.15, icp_dist_thresh=0.5, skip_t_align=False):
    """
    Implementação Corrigida do Algoritmo 1: OBBP-ICP
    """
    # ---------------------------------------------------------
    # STEP 1: Preprocessing
    # ---------------------------------------------------------
    scan_down = scan_raw.voxel_down_sample(voxel_size)
    bim_down = bim_raw.voxel_down_sample(voxel_size)
    
    scan_center = scan_down.get_center()
    bim_center = bim_down.get_center()
    
    T_align = np.eye(4)
    T_align[:3, 3] = bim_center - scan_center
    scan_trans = copy.deepcopy(scan_down).transform(T_align)
    
    R_z = np.eye(4)
    scan_z = copy.deepcopy(scan_trans).transform(R_z)
    
    # O centro atual do scan_z (usaremos isso para girar no próprio eixo)
    current_scan_center = scan_z.get_center()
    
    # ---------------------------------------------------------
    # STEP 2: Bounding Box Alignment
    # ---------------------------------------------------------
    (axis_scan_long, _), (axis_scan_short, _) = get_2d_main_axes(scan_z)
    (axis_bim_long, ext_bim_l), (axis_bim_short, ext_bim_s) = get_2d_main_axes(bim_down)
    
    candidates = []
    is_square = abs(ext_bim_l - ext_bim_s) / max(ext_bim_l, ext_bim_s) <= square_tol
    
    if is_square:
        align_targets = [axis_bim_long, axis_bim_short, -axis_bim_long, -axis_bim_short]
    else:
        align_targets = [axis_bim_long, -axis_bim_long]
        
    for target_vector in align_targets:
        # Matriz de rotação pura
        R_rot = rotation_matrix_2d_to_4x4(axis_scan_long, target_vector)
        
        # CORREÇÃO: Matriz para rotacionar ao redor do próprio centro, não do (0,0,0)
        T_to_origin = np.eye(4)
        T_to_origin[:3, 3] = -current_scan_center
        
        T_to_center = np.eye(4)
        T_to_center[:3, 3] = current_scan_center
        
        # Encadeamento: Vai pra origem -> Gira -> Volta pro lugar (se lê da direita para esquerda)
        R_align_i = T_to_center @ R_rot @ T_to_origin
        
        scan_cand_i = copy.deepcopy(scan_z).transform(R_align_i)
        candidates.append((R_align_i, scan_cand_i))

    # ---------------------------------------------------------
    # STEP 3 & 4: Refinement with ICP & Select Best Alignment
    # ---------------------------------------------------------
    best_fitness = -1.0
    R_best = np.eye(4)
    M_icp_best = np.eye(4)
    
    criteria = o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=50)
    
    for R_align_i, scan_cand_i in candidates:
        icp_result = o3d.pipelines.registration.registration_icp(
            scan_cand_i, bim_down, icp_dist_thresh, np.eye(4),
            o3d.pipelines.registration.TransformationEstimationPointToPoint(),
            criteria
        )
        
        if icp_result.fitness > best_fitness:
            best_fitness = icp_result.fitness
            R_best = R_align_i
            M_icp_best = icp_result.transformation
            
    # Combina as transformações
    M_total = M_icp_best @ R_best @ R_z @ T_align

    # ---------------------------------------------------------
    # STEP 5: Final Transformation and Output
    # ---------------------------------------------------------
    scan_regis = copy.deepcopy(scan_raw).transform(M_total)
    
    distances = scan_regis.compute_point_cloud_distance(bim_raw)
    d_avg = np.mean(distances) if len(distances) > 0 else float('inf')
    
    return scan_regis, d_avg, M_total

# =========================================================
# Bloco de Execução Principal
# =========================================================
if __name__ == "__main__":
    # 1. Defina os caminhos dos seus arquivos .ply
    scan_path = "../AsBuilt/SEGMENTED AOE D19 cloudpoint.ply"
    bim_path = "../AsPlanned/asplanned_pointcloud_d19.ply"
    
    print("Carregando nuvens de pontos...")
    scan_raw = o3d.io.read_point_cloud(scan_path)
    bim_raw = o3d.io.read_point_cloud(bim_path)
    
    # Validação rápida de carregamento
    if not scan_raw.has_points() or not bim_raw.has_points():
        print("Erro: Falha ao carregar as nuvens. Verifique os caminhos dos arquivos.")
        exit()

    # 2. Colorir as nuvens para visualização (Opcional, mas recomendado)
    # Scan Original = Vermelho, BIM = Azul, Scan Registrado = Verde
    scan_raw.paint_uniform_color([1.0, 0.0, 0.0]) # Vermelho
    bim_raw.paint_uniform_color([0.0, 0.0, 1.0])  # Azul
    
    print("Visualizando estado inicial (Scan = Vermelho, BIM = Azul). Feche a janela para continuar...")
    o3d.visualization.draw_geometries([scan_raw, bim_raw], window_name="Estado Inicial")
    
    # 3. Executar o algoritmo OBBP-ICP
    print("Executando OBBP-ICP...")
    # Ajuste voxel_size e icp_dist_thresh dependendo da escala do seu modelo (metros ou milímetros)
    scan_regis, d_avg, m_total = obbp_icp_corrigido(scan_raw, bim_raw, voxel_size=0.2, icp_dist_thresh=20.0)
    
    print("--------------------------------------------------")
    print(f"Alinhamento concluído!")
    print(f"Distância Média (D_avg): {d_avg:.4f}")
    print(f"Matriz de Transformação Final (M_total):\n{m_total}")
    print("--------------------------------------------------")
    
    # 4. Visualizar o resultado final
    scan_regis.paint_uniform_color([0.0, 1.0, 0.0]) # Verde
    
    print("Visualizando resultado final (Scan Registrado = Verde, BIM = Azul).")
    o3d.visualization.draw_geometries([scan_regis, bim_raw], window_name="Resultado Final OBBP-ICP")