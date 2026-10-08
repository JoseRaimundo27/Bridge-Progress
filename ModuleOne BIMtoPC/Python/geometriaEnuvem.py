from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import open3d as o3d
import numpy as np

from ifc_utils import elementos_construidos

PASTA_SCRIPT = Path(__file__).resolve().parent


def extrair_geometria_e_gerar_nuvem(ifc_file_path, densidade_pontos_m2=50, pontos_minimos=100):
    """
    Gera a nuvem as-planned amostrando a superfície de cada elemento.

    O número de pontos de cada elemento é proporcional à sua área (densidade_pontos_m2),
    para que a densidade da nuvem seja homogênea: um tabuleiro de 50 m recebe mais pontos
    que um aparelho de apoio. pontos_minimos garante que elementos pequenos continuem visíveis.
    """
    print(f"Lendo geometria de: {ifc_file_path}...")
    model = ifcopenshell.open(str(ifc_file_path))

    # Filtramos os mesmos elementos físicos do script anterior
    elementos = elementos_construidos(model)

    # Inicia o motor de geometria do IfcOpenShell
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)#usar coordenadas reais

    # Cria diretório para armazenar as peças separadas por GlobalID
    pasta_elementos = PASTA_SCRIPT / "resultados_geometricos"
    pasta_elementos.mkdir(parents=True, exist_ok=True)

    # Variável para armazenar a nuvem de toda a obra junta
    nuvem_global = o3d.geometry.PointCloud()
    sucessos = 0
    sem_geometria = 0
    erros = []

    for elem in elementos:
        # Pula elementos que não possuem representação física 3D
        if not elem.Representation:
            sem_geometria += 1
            continue

        try:
            # 1. EXTRAÇÃO GEOMÉTRICA (Malha 3D do IfcOpenShell)
            shape = ifcopenshell.geom.create_shape(settings, elem)

            # Extrai os dados brutos de vértices e faces (triângulos)
            verts = shape.geometry.verts
            faces = shape.geometry.faces

            # Converte as listas planas do IFC para matrizes matemáticas 3D (Nx3)
            np_verts = np.array(verts).reshape((-1, 3))
            np_faces = np.array(faces).reshape((-1, 3))

            # Constrói a malha (mesh) no formato do Open3D
            mesh = o3d.geometry.TriangleMesh()
            mesh.vertices = o3d.utility.Vector3dVector(np_verts)
            mesh.triangles = o3d.utility.Vector3iVector(np_faces)

            # Calcula as normais das faces (necessário para o algoritmo trabalhar)
            mesh.compute_vertex_normals()

            # 2. AS-PLANNED POINT CLOUD (Poisson Disk Algorithm)
            # Número de pontos proporcional à área do elemento (densidade homogênea)
            n_pontos = max(pontos_minimos, int(mesh.get_surface_area() * densidade_pontos_m2))
            # init_factor gera uma nuvem densa provisória para o Poisson filtrar em seguida
            pcd_elemento = mesh.sample_points_poisson_disk(
                number_of_points=n_pontos,
                init_factor=5
            )

            # Pinta os pontos de cinza para melhor contraste no visualizador
            pcd_elemento.paint_uniform_color([0.6, 0.6, 0.6])

            # Salva o arquivo individual nomeado pelo GlobalID
            caminho_arquivo = pasta_elementos / f"{elem.GlobalId}.ply"
            if not o3d.io.write_point_cloud(str(caminho_arquivo), pcd_elemento):
                raise IOError(f"falha ao salvar {caminho_arquivo}")

            # Adiciona os pontos da peça à nuvem completa da obra
            nuvem_global += pcd_elemento
            sucessos += 1

        except Exception as e:
            erros.append((elem.GlobalId, elem.is_a(), str(e)))

    print(f"Processamento concluído. {sucessos} de {len(elementos)} elementos extraídos e convertidos.")
    if sem_geometria:
        print(f"{sem_geometria} elementos sem representação geométrica foram ignorados.")
    if erros:
        print(f"{len(erros)} elementos falharam:")
        for global_id, tipo, mensagem in erros:
            print(f"  {global_id} ({tipo}): {mensagem}")

    # Exporta a nuvem as-planned unificada
    pasta_global = PASTA_SCRIPT / "resultado_nuvem_global"
    pasta_global.mkdir(parents=True, exist_ok=True)
    arquivo_global = pasta_global / "modelo_as_planned_global.ply"
    if not o3d.io.write_point_cloud(str(arquivo_global), nuvem_global):
        raise IOError(f"Falha ao salvar a nuvem global em: {arquivo_global}")
    print(f"Nuvem global salva em: {arquivo_global}")

    return nuvem_global

if __name__ == "__main__":
    caminho_ifc = PASTA_SCRIPT.parent / "Modelos" / "RSP-116RJ-218-226-ACA-EXE-MB-L2-019-R01-2X3.ifc"

    nuvem_as_planned = extrair_geometria_e_gerar_nuvem(caminho_ifc)

    # 3. Visualização (Abre uma janela 3D com o resultado)
    print("Abrindo visualizador 3D do Open3D... (Use o mouse para rotacionar)")
    o3d.visualization.draw_geometries([nuvem_as_planned], window_name="Nuvem de Pontos As-Planned")
