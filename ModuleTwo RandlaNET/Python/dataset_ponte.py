import glob
import os
from pathlib import Path

import numpy as np
from plyfile import PlyData

from open3d._ml3d.datasets.base_dataset import BaseDataset
from open3d._ml3d.datasets.base_dataset import BaseDatasetSplit

# Caminhos relativos à pasta do módulo ("ModuleTwo RandlaNET/"), válidos em qualquer máquina
PASTA_SCRIPT = Path(__file__).resolve().parent
PASTA_DATASET = PASTA_SCRIPT.parent / "DATASET"
PASTA_PONTE_CUSTOM3D = PASTA_DATASET / "Ponte_Custom3D"
PASTA_LOGS = PASTA_SCRIPT / "logs_ponte"
CHECKPOINT_FINAL = PASTA_LOGS / "RandLANet_PonteDataset_torch" / "checkpoint" / "ckpt_00050.pth"


def carregar_ply(arquivo):
    """
    Lê um PLY (x y z red green blue [label]) e retorna (points, feat, labels).

    As coordenadas são centralizadas em float64 ANTES da conversão para float32:
    com coordenadas UTM (~7 500 000 m) o float32 só tem ~0,5 m de precisão,
    o que destruiria a geometria se a conversão fosse feita antes.
    labels é None se o arquivo não tiver o campo "label".
    """
    vertex = PlyData.read(arquivo)["vertex"].data

    points = np.vstack([
        vertex["x"],
        vertex["y"],
        vertex["z"]
    ]).T.astype(np.float64)
    points = (points - np.min(points, axis=0)).astype(np.float32)

    feat = np.vstack([
        vertex["red"],
        vertex["green"],
        vertex["blue"]
    ]).T.astype(np.float32) / 255.0

    labels = None
    if "label" in vertex.dtype.names:
        labels = np.array(vertex["label"]).astype(np.int32)

    return points, feat, labels


def contar_pontos_ply(arquivo):
    """Lê apenas o cabeçalho do PLY para obter o número de pontos (sem carregar a nuvem)."""
    with open(arquivo, "rb") as f:
        for linha in f:
            partes = linha.decode("ascii", errors="ignore").split()
            if partes[:2] == ["element", "vertex"]:
                return int(partes[2])
            if partes[:1] == ["end_header"]:
                break
    return 0


class PonteDataset(BaseDataset):
    def __init__(self, dataset_path=PASTA_PONTE_CUSTOM3D, **kwargs):
        dataset_path = str(dataset_path)
        super().__init__(
            dataset_path=dataset_path,
            name="PonteDataset",
            **kwargs
        )

        # 1. Definindo as 2 classes da nossa ponte
        self.label_to_names = self.get_label_to_names()

        self.num_classes = 2
        self.cfg.use_cache = False

        # Apontando para as pastas corretas onde você deve colocar os arquivos .ply
        self.train_files = sorted(glob.glob(os.path.join(dataset_path, "train", "*.ply")))
        self.val_files = sorted(glob.glob(os.path.join(dataset_path, "val", "*.ply")))
        self.test_files = sorted(glob.glob(os.path.join(dataset_path, "test", "*.ply")))

        # Sem pasta test/, o teste usa a validação: as métricas ficam otimistas
        # (esses arquivos já serviram para escolher o modelo durante o treino)
        if not self.test_files:
            print(f"AVISO: nenhum arquivo em {dataset_path}/test/. "
                  "O teste vai usar os arquivos de validação e as métricas serão otimistas.")
            self.test_files = self.val_files

    @staticmethod
    def get_label_to_names():
        return {
            0: "floor",
            1: "column"
        }

    def is_tested(self, attr):
        return False

    def save_test_result(self, results, attr):
        pass

    def get_split_list(self, split):
        if split == "train":
            return self.train_files
        elif split in ["val", "validation"]:
            return self.val_files
        elif split == "test":
            return self.test_files
        else:
            raise ValueError("split inválido")

    def get_split(self, split):
        return PonteSplit(self, split, self.get_split_list(split))


class PonteSplit(BaseDatasetSplit):
    def __init__(self, dataset, split, files):
        self.files = files
        super().__init__(dataset, split=split)

    def __len__(self):
        # TRUQUE: Multiplicamos por 100 para forçar a IA a treinar mais vezes
        return len(self.files) * 100

    def get_data(self, idx):
        # TRUQUE: Usamos o (%) para ele ler sempre o mesmo arquivo sem dar erro
        file = self.files[idx % len(self.files)]

        print(f"[{self.split}] Carregando arquivo: {file}")

        points, feat, labels = carregar_ply(file)
        if labels is None:
            raise ValueError(f"O arquivo {file} não tem o campo 'label'.")

        return {
            "point": points,
            "feat": feat,
            "label": labels
        }

    def get_attr(self, idx):
        # TRUQUE AQUI TAMBÉM: usar o módulo para ele repetir o arquivo corretamente
        file = self.files[idx % len(self.files)]

        name = os.path.splitext(os.path.basename(file))[0]
        return {
            "idx": idx,
            "name": name,
            "path": file,
            "split": self.split,
            "num_points": contar_pontos_ply(file)
        }
