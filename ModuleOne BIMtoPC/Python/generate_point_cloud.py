from pathlib import Path

import open3d as o3d

PASTA_SCRIPT = Path(__file__).resolve().parent
PASTA_MALHAS = PASTA_SCRIPT.parent / "Results"/ "resultados_geometricos" / "d19"      # saída de extrair_geometria.py
PASTA_NUVENS = PASTA_SCRIPT.parent / "Results"/  "resultados_nuvens_elementos" / "d19"    # uma nuvem .ply por elemento
PASTA_GLOBAL =  PASTA_SCRIPT.parent / "Results"/ "resultado_nuvem_global" / "d19"


def gerar_nuvem_as_planned(pasta_malhas=PASTA_MALHAS, densidade_pontos_m2=50, pontos_minimos=100):
    """
    Gera a nuvem as-planned amostrando a superfície de cada malha salva.

    O número de pontos de cada elemento é proporcional à sua área (densidade_pontos_m2),
    para que a densidade da nuvem seja homogênea: um tabuleiro de 50 m recebe mais pontos
    que um aparelho de apoio. pontos_minimos garante que elementos pequenos continuem visíveis.
    """
    pasta_malhas = Path(pasta_malhas)
    arquivos_malhas = sorted(pasta_malhas.glob("*.ply"))
    if not arquivos_malhas:
        raise FileNotFoundError(
            f"Nenhuma malha encontrada em {pasta_malhas}. Execute extrair_geometria.py primeiro."
        )

    PASTA_NUVENS.mkdir(parents=True, exist_ok=True)
    PASTA_GLOBAL.mkdir(parents=True, exist_ok=True)

    # Nuvem de toda a obra junta
    nuvem_global = o3d.geometry.PointCloud()
    sucessos = 0
    erros = []

    for arquivo in arquivos_malhas:
        global_id = arquivo.stem
        try:
            mesh = o3d.io.read_triangle_mesh(str(arquivo))
            if not mesh.has_triangles():
                raise ValueError("malha vazia")

            # Normais necessárias para o algoritmo de amostragem
            mesh.compute_vertex_normals()

            # Número de pontos proporcional à área do elemento (densidade homogênea)
            n_pontos = max(pontos_minimos, int(mesh.get_surface_area() * densidade_pontos_m2))

            # init_factor gera uma nuvem densa provisória para o Poisson filtrar em seguida
            pcd_elemento = mesh.sample_points_poisson_disk(
                number_of_points=n_pontos,
                init_factor=5
            )

            # Pinta os pontos de cinza para melhor contraste no visualizador
            pcd_elemento.paint_uniform_color([0.6, 0.6, 0.6])

            # Salva a nuvem individual nomeada pelo GlobalID
            caminho_arquivo = PASTA_NUVENS / f"{global_id}.ply"
            if not o3d.io.write_point_cloud(str(caminho_arquivo), pcd_elemento):
                raise IOError(f"falha ao salvar {caminho_arquivo}")

            # Adiciona os pontos da peça à nuvem completa da obra
            nuvem_global += pcd_elemento
            sucessos += 1

        except Exception as e:
            erros.append((global_id, str(e)))

    print(f"Processamento concluído. {sucessos} de {len(arquivos_malhas)} malhas convertidas em nuvem.")
    if erros:
        print(f"{len(erros)} elementos falharam:")
        for global_id, mensagem in erros:
            print(f"  {global_id}: {mensagem}")

    # Exporta a nuvem as-planned unificada
    arquivo_global = PASTA_GLOBAL / "modelo_as_planned_global.ply"
    if not o3d.io.write_point_cloud(str(arquivo_global), nuvem_global):
        raise IOError(f"Falha ao salvar a nuvem global em: {arquivo_global}")
    print(f"Nuvem global salva em: {arquivo_global}")

    return nuvem_global


if __name__ == "__main__":
    nuvem_as_planned = gerar_nuvem_as_planned()

    # Visualização (abre uma janela 3D com o resultado)
    print("Abrindo visualizador 3D do Open3D... (Use o mouse para rotacionar)")
    o3d.visualization.draw_geometries([nuvem_as_planned], window_name="Nuvem de Pontos As-Planned")