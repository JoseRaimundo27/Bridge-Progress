from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import open3d as o3d
import numpy as np

from utils.ifc_utils import elementos_construidos

PASTA_SCRIPT = Path(__file__).resolve().parent
PASTA_MALHAS = PASTA_SCRIPT.parent / "Results" / "resultados_geometricos" / "d19"


def extrair_geometria(ifc_file_path, pasta_saida=PASTA_MALHAS):
    """
    Extrai a malha 3D (vértices e triângulos, em coordenadas reais) de cada
    elemento construído do IFC e salva um arquivo <GlobalId>.ply por elemento.

    Retorna a lista de caminhos das malhas salvas.
    """
    print(f"Lendo geometria de: {ifc_file_path}...")
    model = ifcopenshell.open(str(ifc_file_path))

    # Filtra os elementos físicos do modelo
    elementos = elementos_construidos(model)

    # Inicia o motor de geometria do IfcOpenShell
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)  # usar coordenadas reais

    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    arquivos = []
    sem_geometria = 0
    erros = []

    for elem in elementos:
        # Pula elementos que não possuem representação física 3D
        if not elem.Representation:
            sem_geometria += 1
            continue

        try:
            shape = ifcopenshell.geom.create_shape(settings, elem)

            # Converte as listas planas do IFC para matrizes Nx3
            np_verts = np.array(shape.geometry.verts).reshape((-1, 3))
            np_faces = np.array(shape.geometry.faces).reshape((-1, 3))

            if len(np_faces) == 0:
                raise ValueError("malha sem triângulos")

            # Constrói a malha no formato do Open3D
            mesh = o3d.geometry.TriangleMesh()
            mesh.vertices = o3d.utility.Vector3dVector(np_verts)
            mesh.triangles = o3d.utility.Vector3iVector(np_faces)

            # Salva a malha nomeada pelo GlobalID
            caminho_arquivo = pasta_saida / f"{elem.GlobalId}.ply"
            if not o3d.io.write_triangle_mesh(str(caminho_arquivo), mesh):
                raise IOError(f"falha ao salvar {caminho_arquivo}")

            arquivos.append(caminho_arquivo)

        except Exception as e:
            erros.append((elem.GlobalId, elem.is_a(), str(e)))

    print(f"Extração concluída. {len(arquivos)} de {len(elementos)} malhas salvas em: {pasta_saida}")
    if sem_geometria:
        print(f"{sem_geometria} elementos sem representação geométrica foram ignorados.")
    if erros:
        print(f"{len(erros)} elementos falharam:")
        for global_id, tipo, mensagem in erros:
            print(f"  {global_id} ({tipo}): {mensagem}")

    return arquivos


if __name__ == "__main__":
    caminho_ifc = PASTA_SCRIPT.parent / "Models" /"d19"/ "RSP-116RJ-218-226-ACA-EXE-MB-L2-019-R01-2X3.ifc"
    extrair_geometria(caminho_ifc)