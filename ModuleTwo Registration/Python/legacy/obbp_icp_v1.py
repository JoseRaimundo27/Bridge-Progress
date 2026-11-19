import os
import open3d as o3d
import numpy as np
import copy
import math
import matplotlib.pyplot as plt


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
        return (axis_0, length_0), (axis_1, length_1)  # Long, Short
    else:
        return (axis_1, length_1), (axis_0, length_0)  # Long, Short


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


def overlap_region_metrics(scan_regis, bim_raw, cell_size=None, min_cell_points=10, use_z=False):
    """
    Calcula as distâncias apenas na região onde os DOIS modelos têm pontos.

    Ideia:
      1. Divide o espaço em uma grade de células (2D em XY, ou 3D se use_z=True).
      2. Uma célula é "ocupada" por uma nuvem se tiver pelo menos min_cell_points pontos dela.
      3. A região de sobreposição é o conjunto de células ocupadas pelo scan E pelo BIM.
      4. Só os pontos que caem nessas células são avaliados:
           - pontos do scan na sobreposição -> distância até o BIM COMPLETO
           - pontos do BIM na sobreposição  -> distância até o scan COMPLETO
         (o alvo é a nuvem completa para que os pontos na borda da região
          não sejam penalizados artificialmente.)

    A região é escolhida pela presença de pontos, e não pela distância, então
    o recorte não favorece valores pequenos. Extremos de um modelo sem
    correspondente no outro (em qualquer direção) ficam de fora automaticamente.

    cell_size: tamanho da célula (m). Se None, usa 1/50 da diagonal em XY da união
               das duas nuvens. Células muito pequenas fragmentam a região; células
               muito grandes incluem trechos sem correspondente.
    min_cell_points: mínimo de pontos de cada nuvem para a célula contar como ocupada.
    use_z: True inclui a altura na grade (útil se um modelo tem partes em cotas
           que o outro não cobre).
    """
    scan_pts = np.asarray(scan_regis.points)
    bim_pts = np.asarray(bim_raw.points)

    dims = 3 if use_z else 2
    lo = np.minimum(scan_pts.min(axis=0), bim_pts.min(axis=0))[:dims]
    hi = np.maximum(scan_pts.max(axis=0), bim_pts.max(axis=0))[:dims]

    if cell_size is None:
        cell_size = float(np.linalg.norm((hi - lo)[:2]) / 50.0)

    idx_s = np.floor((scan_pts[:, :dims] - lo) / cell_size).astype(np.int64)
    idx_b = np.floor((bim_pts[:, :dims] - lo) / cell_size).astype(np.int64)
    shape = np.maximum(idx_s.max(axis=0), idx_b.max(axis=0)) + 1

    key_s = np.ravel_multi_index(idx_s.T, shape)
    key_b = np.ravel_multi_index(idx_b.T, shape)

    cells_s, counts_s = np.unique(key_s, return_counts=True)
    cells_b, counts_b = np.unique(key_b, return_counts=True)
    occupied_s = cells_s[counts_s >= min_cell_points]
    occupied_b = cells_b[counts_b >= min_cell_points]
    overlap_cells = np.intersect1d(occupied_s, occupied_b)

    mask_s = np.isin(key_s, overlap_cells)
    mask_b = np.isin(key_b, overlap_cells)

    result = {
        "cell_size": cell_size,
        "n_overlap_cells": int(len(overlap_cells)),
        "frac_scan_kept": float(mask_s.mean()),
        "frac_bim_kept": float(mask_b.mean()),
        "mask_scan": mask_s,
        "mask_bim": mask_b,
    }

    if mask_s.sum() == 0 or mask_b.sum() == 0:
        result.update({
            "d_avg": float("inf"), "d_scan_to_bim": float("inf"), "d_bim_to_scan": float("inf"),
            "median": float("inf"), "p95": float("inf"), "max": float("inf"),
        })
        return result

    scan_in = scan_regis.select_by_index(np.flatnonzero(mask_s))
    bim_in = bim_raw.select_by_index(np.flatnonzero(mask_b))

    d_s2b = np.asarray(scan_in.compute_point_cloud_distance(bim_raw))
    d_b2s = np.asarray(bim_in.compute_point_cloud_distance(scan_regis))
    d_all = np.concatenate([d_s2b, d_b2s])

    result.update({
        "d_avg": float((d_s2b.mean() + d_b2s.mean()) / 2.0),
        "d_scan_to_bim": float(d_s2b.mean()),
        "d_bim_to_scan": float(d_b2s.mean()),
        "median": float(np.median(d_all)),
        "p95": float(np.percentile(d_all, 95)),
        "max": float(d_all.max()),
    })
    return result


def print_overlap_metrics(m):
    print("--------------------------------------------------")
    print("Métricas na região de sobreposição (scan e BIM)")
    print(f"tamanho da célula: {m['cell_size']:.2f} m   células de sobreposição: {m['n_overlap_cells']}")
    print(f"scan mantido: {m['frac_scan_kept'] * 100:.1f}%   BIM mantido: {m['frac_bim_kept'] * 100:.1f}%")
    print(f"D_avg (simétrico):      {m['d_avg']:.4f} m")
    print(f"  scan -> BIM:          {m['d_scan_to_bim']:.4f} m")
    print(f"  BIM -> scan:          {m['d_bim_to_scan']:.4f} m")
    print(f"mediana (2 direções):   {m['median']:.4f} m")
    print(f"p95     (2 direções):   {m['p95']:.4f} m")
    print(f"max     (2 direções):   {m['max']:.4f} m")
    print("--------------------------------------------------")


def show_overlap(scan_regis, bim_raw, m, png_path="sobreposicao_topo.png", n=100000):
    """
    Mostra a região usada: scan mantido = verde, BIM mantido = azul,
    pontos excluídos = cinza. Abre no Open3D e salva uma vista de topo em PNG.
    """
    mask_s, mask_b = m["mask_scan"], m["mask_bim"]

    scan_vis = copy.deepcopy(scan_regis)
    bim_vis = copy.deepcopy(bim_raw)

    colors_s = np.tile([0.35, 0.35, 0.35], (len(mask_s), 1))
    colors_s[mask_s] = [0.0, 0.8, 0.0]
    colors_b = np.tile([0.75, 0.75, 0.75], (len(mask_b), 1))
    colors_b[mask_b] = [0.0, 0.0, 1.0]
    scan_vis.colors = o3d.utility.Vector3dVector(colors_s)
    bim_vis.colors = o3d.utility.Vector3dVector(colors_b)

    rng = np.random.default_rng(0)
    fig, ax = plt.subplots(figsize=(10, 10))
    for pcd, colors, nome in [(bim_vis, colors_b, "BIM"), (scan_vis, colors_s, "scan")]:
        pts = np.asarray(pcd.points)
        idx = rng.choice(len(pts), size=min(n, len(pts)), replace=False)
        ax.scatter(pts[idx, 0], pts[idx, 1], s=0.2, c=colors[idx], alpha=0.6)
    ax.set_aspect("equal")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_title("Verde = scan usado | Azul = BIM usado | Cinza = excluído")
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
    print(f"Vista de topo da sobreposição salva em: {png_path}")

    print("Visualizando sobreposição (verde = scan usado, azul = BIM usado, cinza = excluído). Feche a janela para continuar...")
    o3d.visualization.draw_geometries([bim_vis, scan_vis], window_name="Região de sobreposição")


def obbp_icp_corrigido(scan_raw, bim_raw, voxel_size=0.1, square_tol=0.15, icp_dist_thresh=0.5,
                       cell_size=None, min_cell_points=10, use_z=False):
    """
    Implementação Corrigida do Algoritmo 1: OBBP-ICP, com o D_avg calculado
    apenas na região de sobreposição entre scan e BIM.
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

    # O centro atual do scan_z (usado para girar no próprio eixo)
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
        R_rot = rotation_matrix_2d_to_4x4(axis_scan_long, target_vector)

        T_to_origin = np.eye(4)
        T_to_origin[:3, 3] = -current_scan_center

        T_to_center = np.eye(4)
        T_to_center[:3, 3] = current_scan_center

        # Vai pra origem -> Gira -> Volta pro lugar (lê-se da direita para a esquerda)
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

    metrics = overlap_region_metrics(
        scan_regis, bim_raw,
        cell_size=cell_size,
        min_cell_points=min_cell_points,
        use_z=use_z,
    )

    return scan_regis, metrics, M_total


# =========================================================
# Bloco de Execução Principal
# =========================================================
if __name__ == "__main__":
    # 1. Caminhos dos arquivos .ply
    scan_path = "../../AsBuilt/S07/Segmented S07.ply"
    bim_path = "../../AsPlanned/S07/s07_without_piles.ply"

    print("Carregando nuvens de pontos...")
    scan_raw = o3d.io.read_point_cloud(scan_path)
    bim_raw = o3d.io.read_point_cloud(bim_path)

    if not scan_raw.has_points() or not bim_raw.has_points():
        print("Erro: Falha ao carregar as nuvens. Verifique os caminhos dos arquivos.")
        exit()

    # 2. Colorir as nuvens para visualização
    # Scan Original = Vermelho, BIM = Azul, Scan Registrado = Verde
    scan_raw.paint_uniform_color([1.0, 0.0, 0.0])
    bim_raw.paint_uniform_color([0.0, 0.0, 1.0])

    print("Visualizando estado inicial (Scan = Vermelho, BIM = Azul). Feche a janela para continuar...")
    o3d.visualization.draw_geometries([scan_raw, bim_raw], window_name="Estado Inicial")

    # 3. Executar o algoritmo OBBP-ICP
    # Coordenadas em UTM -> unidade em metros. icp_dist_thresh=20.0 significa 20 m.
    # cell_size=None -> automático (1/50 da diagonal em XY). use_z=True inclui a altura na grade.
    print("Executando OBBP-ICP...")
    scan_regis, metrics, m_total = obbp_icp_corrigido(
        scan_raw, bim_raw,
        voxel_size=0.2,
        icp_dist_thresh=20.0,
        cell_size=None,
        min_cell_points=10,
        use_z=False,
    )

    print("--------------------------------------------------")
    print("Alinhamento concluído!")
    print(f"Matriz de Transformação Final (M_total):\n{m_total}")
    print("--------------------------------------------------")
    print_overlap_metrics(metrics)

    # 4. Visualizar a região de sobreposição usada na métrica
    show_overlap(scan_regis, bim_raw, metrics)

    # 5. Salvar o As-Built registrado em PLY
    output_path = "../Results/s07_asbuilt_registered.ply"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Recarrega o scan original (sem a pintura) e aplica a transformação final
    scan_registrado_final = o3d.io.read_point_cloud(scan_path)
    scan_registrado_final.transform(m_total)

    ok = o3d.io.write_point_cloud(output_path, scan_registrado_final)
    if ok:
        print(f"As-Built registrado salvo em: {output_path}")
    else:
        print("Erro ao salvar o arquivo PLY.")