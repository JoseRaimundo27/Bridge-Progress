import os
import ifcopenshell
import ifcopenshell.geom
import open3d as o3d
import numpy as np

def extrair_geometria_e_gerar_nuvem(ifc_file_path, pontos_por_elemento=2000):
    print(f"Lendo geometria de: {ifc_file_path}...")
    model = ifcopenshell.open(ifc_file_path)
    
    # Filtramos os mesmos elementos físicos do script anterior
    elementos = model.by_type("IfcBuildingElement")
    
    # Inicia o motor de geometria do IfcOpenShell
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)#usar coordenadas reais
    
    # Cria diretório para armazenar as peças separadas por GlobalID
    os.makedirs("resultados_geometricos", exist_ok=True)
    
    # Variável para armazenar a nuvem de toda a obra junta
    nuvem_global = o3d.geometry.PointCloud()
    sucessos = 0
    
    for elem in elementos:
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
            # init_factor gera uma nuvem densa provisória para o Poisson filtrar em seguida
            pcd_elemento = mesh.sample_points_poisson_disk(
                number_of_points=pontos_por_elemento, 
                init_factor=5
            )
            
            # Pinta os pontos de cinza para melhor contraste no visualizador
            pcd_elemento.paint_uniform_color([0.6, 0.6, 0.6])
            
            # Salva o arquivo individual nomeado pelo GlobalID
            caminho_arquivo = f"resultados_geometricos/{elem.GlobalId}.ply"
            o3d.io.write_point_cloud(caminho_arquivo, pcd_elemento)
            
            # Adiciona os pontos da peça à nuvem completa da obra
            nuvem_global += pcd_elemento
            sucessos += 1
            
        except Exception as e:
            # Pula elementos que não possuem representação física 3D válida
            pass

    print(f"Processamento concluído. {sucessos} de {len(elementos)} elementos extraídos e convertidos.")
    
    # Exporta a nuvem as-planned unificada
    arquivo_global = "resultado_nuvem_global/modelo_as_planned_global.ply"
    o3d.io.write_point_cloud(arquivo_global, nuvem_global)
    print(f"Nuvem global salva em: {arquivo_global}")
    
    return nuvem_global

if __name__ == "__main__":
    caminho_ifc = "../Modelos/RSP-116RJ-218-226-ACA-EXE-MB-L2-019-R01-2X3.ifc" 
    
    nuvem_as_planned = extrair_geometria_e_gerar_nuvem(caminho_ifc)
    
    # 3. Visualização (Abre uma janela 3D com o resultado)
    print("Abrindo visualizador 3D do Open3D... (Use o mouse para rotacionar)")
    o3d.visualization.draw_geometries([nuvem_as_planned], window_name="Nuvem de Pontos As-Planned")