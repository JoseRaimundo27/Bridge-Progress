from pathlib import Path

import numpy as np

PASTA_DATASET = Path(__file__).resolve().parent.parent / "DATASET"

#txt_path = PASTA_DATASET / "Ponte_Custom3D" / "train" / "ponte.txt"
#ply_path = PASTA_DATASET / "Ponte_Custom3D" / "train" / "ponte.ply"
txt_path = PASTA_DATASET / "D19" / "ponte.txt"
ply_path = PASTA_DATASET / "D19" / "ponte.ply"

print("Lendo o arquivo TXT...")
data = np.loadtxt(txt_path)

num_points = data.shape[0]

print("Escrevendo o arquivo PLY...")
with open(ply_path, 'w') as f:
    # Escrevendo o cabeçalho oficial do PLY
    f.write("ply\n")
    f.write("format ascii 1.0\n")
    f.write(f"element vertex {num_points}\n")
    # double (float64): em float32 coordenadas UTM perdem a precisão (~0,5 m)
    f.write("property double x\n")
    f.write("property double y\n")
    f.write("property double z\n")
    f.write("property uchar red\n")
    f.write("property uchar green\n")
    f.write("property uchar blue\n")
    f.write("property int label\n")  # A IA vai ler as classes por aqui!
    f.write("end_header\n")
    
    # Escrevendo os pontos
    for row in data:
        x, y, z = row[0], row[1], row[2]
        # Cores precisam ser inteiros no PLY (0-255)
        r, g, b = int(row[3]), int(row[4]), int(row[5])
        label = int(row[6])
        f.write(f"{x} {y} {z} {r} {g} {b} {label}\n")

print(f"Sucesso! Arquivo salvo em: {ply_path}")