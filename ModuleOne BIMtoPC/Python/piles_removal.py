import shutil
from pathlib import Path

import ifcopenshell

PASTA_SCRIPT = Path(__file__).resolve().parent
PASTA_MALHAS = PASTA_SCRIPT.parent / "Results"/ "resultados_geometricos" / "s07"  # saída de extrair_geometria.py
PASTA_ESTACAS = PASTA_SCRIPT.parent / "Results"/  "estacas_removidas"        # para onde as malhas das estacas são movidas

# Critérios para identificar uma estaca
TIPOS_ESTACA = ("IfcPile",)
TRECHOS_NOME_ESTACA = ("ccr_estaca",)  # comparação em minúsculas


def eh_estaca(elem):
    """True se o elemento é do tipo estaca ou tem nome de estaca (ex.: 'CCR_Estaca:⌀45:2190540')."""
    if elem.is_a() in TIPOS_ESTACA:
        return True
    nome = (getattr(elem, "Name", None) or "").lower()
    return any(trecho in nome for trecho in TRECHOS_NOME_ESTACA)


def listar_estacas(ifc_file_path):
    """Retorna {GlobalId: Nome} de todas as estacas do modelo IFC."""
    model = ifcopenshell.open(str(ifc_file_path))
    return {
        elem.GlobalId: elem.Name
        for elem in model.by_type("IfcProduct")
        if eh_estaca(elem)
    }


def remover_estacas(ifc_file_path, pasta_malhas=PASTA_MALHAS, pasta_estacas=PASTA_ESTACAS):
    """
    Move para 'estacas_removidas/' as malhas (.ply) das estacas, de modo que
    gerar_nuvem.py não as inclua na nuvem global. Nada é apagado: para desfazer,
    basta mover os arquivos de volta.
    """
    pasta_malhas = Path(pasta_malhas)
    pasta_estacas = Path(pasta_estacas)

    if not pasta_malhas.exists():
        raise FileNotFoundError(
            f"Pasta {pasta_malhas} não existe. Execute extrair_geometria.py primeiro."
        )

    print(f"Identificando estacas em: {ifc_file_path}...")
    estacas = listar_estacas(ifc_file_path)
    print(f"{len(estacas)} estacas encontradas no modelo.")

    pasta_estacas.mkdir(parents=True, exist_ok=True)

    movidas = 0
    sem_malha = 0
    for global_id in estacas:
        origem = pasta_malhas / f"{global_id}.ply"
        if not origem.exists():
            sem_malha += 1  # já removida antes, ou falhou na extração
            continue
        shutil.move(str(origem), str(pasta_estacas / origem.name))
        movidas += 1

    restantes = len(list(pasta_malhas.glob("*.ply")))
    print(f"{movidas} malhas de estacas movidas para: {pasta_estacas}")
    if sem_malha:
        print(f"{sem_malha} estacas sem malha na pasta (já removidas ou não extraídas).")
    print(f"{restantes} malhas restantes em {pasta_malhas}.")

    return movidas


if __name__ == "__main__":
    caminho_ifc = PASTA_SCRIPT.parent / "Models" / "s07"/ "RSP-116RJ-218-226-ACA-EXE-MB-L2-007-R01-2x3.ifc"
    remover_estacas(caminho_ifc)