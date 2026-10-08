import torch
import open3d.ml.torch as ml3d
from dataset_ponte import PonteDataset, PASTA_PONTE_CUSTOM3D, PASTA_LOGS

# Carrega o nosso novo e maravilhoso Dataset de PLY
dataset = PonteDataset(
    dataset_path=PASTA_PONTE_CUSTOM3D
)

# Configura a Rede Neural RandLA-Net
model = ml3d.models.RandLANet(
    num_points=40960,  
    num_classes=2,     
    in_channels=6,    
    ignored_label_inds=[]
)

#  Monta o Pipeline de Treino
pipeline = ml3d.pipelines.SemanticSegmentation(
    model=model,
    dataset=dataset,

    max_epoch=50,
    batch_size=2,
    val_batch_size=2,

    optimizer={
        "lr": 1e-3
    },
    scheduler_gamma=0.95,
    num_workers=0,
    main_log_dir=str(PASTA_LOGS),
    device="cuda" if torch.cuda.is_available() else "cpu"
)

print("Iniciando o treinamento na GPU...")
pipeline.run_train()