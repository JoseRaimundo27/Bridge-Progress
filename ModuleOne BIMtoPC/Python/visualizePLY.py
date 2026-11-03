import open3d as o3d

def visualizar_ply(caminho_arquivo):
    # Carrega a nuvem de pontos
    pcd = o3d.io.read_point_cloud(caminho_arquivo)
    
    # Verifica se a nuvem foi carregada corretamente
    if not pcd.has_points():
        print(f"Erro: O arquivo '{caminho_arquivo}' não contém pontos ou não foi encontrado.")
        return

    print(f"Nuvem carregada com sucesso!")
    print(f"Total de pontos: {len(pcd.points)}")

    # Abre a janela interativa de visualização
    o3d.visualization.draw_geometries(
        [pcd],
        window_name="Visualizador de Nuvem de Pontos",
        width=1024,
        height=768
    )

if __name__ == "__main__":
    # Substitua pelo caminho do seu arquivo .ply
    caminho_do_ply = "../Modelos/s07_local_asplanned.ply"
    visualizar_ply(caminho_do_ply)