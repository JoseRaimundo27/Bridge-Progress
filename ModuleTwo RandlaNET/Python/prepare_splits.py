"""Monta as pastas train/val/test do PonteDataset a partir do dataset da equipe.

Dataset: https://huggingface.co/datasets/Gabl26/bridge-pointclouds
    baixado em DATASET/bridge-pointclouds/ (uav_lidar/, semanticbridge/, semanticbridge_synth/),
    a divisão de cada cena está no scenes.csv de cada fonte.
    Campo label: -1 = sem rótulo (ignorar), 0 = não ponte, 1 = ponte.

Saída: DATASET/Ponte_Custom3D/{train,val,test}/ com links simbólicos (nenhuma cópia).
Fontes sem cor (has_rgb = False, ex. semanticbridge_synth) são ignoradas por padrão,
porque o modelo usa as cores como atributos (in_channels=6).

Uso:
    python prepare_splits.py                                  # uav_lidar + semanticbridge
    python prepare_splits.py --sources uav_lidar              # só as pontes de drone
    python prepare_splits.py --sources uav_lidar semanticbridge semanticbridge_synth --allow-no-rgb
"""

import argparse
import csv
import shutil

from dataset_ponte import PASTA_DATASET, PASTA_PONTE_CUSTOM3D

ORIGEM = PASTA_DATASET / "bridge-pointclouds"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sources", nargs="+", default=["uav_lidar", "semanticbridge"])
    parser.add_argument("--allow-no-rgb", action="store_true", help="incluir cenas sem cor")
    args = parser.parse_args()

    if PASTA_PONTE_CUSTOM3D.exists():
        if any(not p.is_symlink() for p in PASTA_PONTE_CUSTOM3D.rglob("*.ply")):
            raise SystemExit(f"{PASTA_PONTE_CUSTOM3D} contém arquivos que não são links: não apagado.")
        shutil.rmtree(PASTA_PONTE_CUSTOM3D)

    contagem = {}
    for fonte in args.sources:
        lista = ORIGEM / fonte / "scenes.csv"
        if not lista.exists():
            raise SystemExit(f"{lista} não encontrado: baixe o dataset (ver docstring).")
        with open(lista, newline="") as f:
            for cena in csv.DictReader(f):
                if cena["has_rgb"] != "True" and not args.allow_no_rgb:
                    continue
                destino = PASTA_PONTE_CUSTOM3D / cena["split"] / cena["file"]
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.symlink_to(ORIGEM / fonte / cena["file"])
                contagem[cena["split"]] = contagem.get(cena["split"], 0) + 1

    print(f"{PASTA_PONTE_CUSTOM3D}: " + ", ".join(f"{s} {n}" for s, n in sorted(contagem.items())))


if __name__ == "__main__":
    main()
