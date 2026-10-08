import os
import glob
from pathlib import Path

import numpy as np
import open3d as o3d

# 1. Caminho para a pasta onde estão suas anotações
PASTA_DATASET = Path(__file__).resolve().parent.parent / "DATASET"
annotations_dir = str(PASTA_DATASET / "Rafaela" / "Segmentacao" / "Backup_Original" / "Annotations")

# 2. Definir as cores para cada classe (Valores entre 0 e 1)
COLOR_MAP = {
    "column": [1.0, 0.0, 0.0],  # Pilares ficarão Vermelhos
    "floor":  [0.0, 0.6, 1.0],  # O chão ficará Azul Claro
}

all_points = []
all_colors = []

# Procurar todos os arquivos .txt na pasta de anotações
txt_files = glob.glob(os.path.join(annotations_dir, "*.txt"))

if not txt_files:
    print(f"Erro: Nenhum arquivo .txt encontrado em {annotations_dir}")
    exit()

print("--- Carregando Elementos da Ponte ---")
for file_path in txt_files:
    filename = os.path.basename(file_path)
    
    # Descobre a classe pelo nome (ex: column_1.txt -> column)
    class_name = filename.split('_')[0]
    
    # Define a cor. Se for uma classe nova que você criar depois, pinta de Cinza [0.5, 0.5, 0.5]
    color = COLOR_MAP.get(class_name, [0.5, 0.5, 0.5])
    
    # Carrega APENAS as colunas 0, 1 e 2 (X, Y, Z)
    # Como limpamos os arquivos, agora isso roda sem erros!
    points = np.loadtxt(file_path, usecols=(0, 1, 2))
    
    if points.ndim == 1:
        points = points.reshape(1, -1)
        
    all_points.append(points)
    
    # Cria uma matriz de cores com o mesmo número de pontos do arquivo
    colors = np.tile(color, (points.shape[0], 1))
    all_colors.append(colors)
    
    print(f" Loaded {filename} | Pontos: {points.shape[0]} | Cor: {class_name}")

# Junta todos os pedaços em uma única nuvem para visualização
combined_points = np.vstack(all_points)
combined_colors = np.vstack(all_colors)

print(f"\nTotal de pontos na cena: {combined_points.shape[0]}")

# 3. Inicializa e exibe a nuvem no Open3D
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(combined_points)
pcd.colors = o3d.utility.Vector3dVector(combined_colors)

print("\nAbrindo janela do Open3D... (Use o mouse para rotacionar/zoom. Pressione 'q' para fechar)")
o3d.visualization.draw_geometries([pcd])