import re
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element
import pandas as pd

from ifc_utils import elementos_construidos

PASTA_SCRIPT = Path(__file__).resolve().parent

# Padrões de busca das datas 4D (comparados com o nome da propriedade em minúsculas).
# Ex.: "Contained in Task Start (Planned)" -> Data_Inicio_Planejado
#      "Contained in Task End (Actual)"    -> Data_Fim_Real
RE_INICIO = re.compile(r"start|in[ií]cio")
RE_FIM = re.compile(r"finish|t[eé]rmino|\bend\b|\bfim\b")
RE_REAL = re.compile(r"\bactual\b|\breal\b")


def classificar_data(chave_lower):
    """Retorna o campo de data correspondente à propriedade, ou None se não for uma data."""
    if RE_INICIO.search(chave_lower):
        evento = "Inicio"
    elif RE_FIM.search(chave_lower):
        evento = "Fim"
    else:
        return None
    tipo = "Real" if RE_REAL.search(chave_lower) else "Planejado"
    return f"Data_{evento}_{tipo}"


def extrair_dados_semanticos(ifc_file_path):
    # 1. Carregamento do arquivo IFC
    print(f"Carregando o arquivo: {ifc_file_path}...")
    model = ifcopenshell.open(str(ifc_file_path))

    # Filtrar apenas elementos físicos de construção (ignora eixos, espaços virtuais, etc.)
    elementos = elementos_construidos(model)
    print(f"Total de elementos físicos encontrados: {len(elementos)}")

    dados_extraidos = []

    for elem in elementos:
        # Pega todos os PropertySets e QuantitySets associados ao elemento
        psets = ifcopenshell.util.element.get_psets(elem)

        # Inicializa variáveis
        campos = {
            "Volume_m3": None,
            "Area_m2": None,
            "Data_Inicio_Planejado": None,
            "Data_Inicio_Real": None,
            "Data_Fim_Planejado": None,
            "Data_Fim_Real": None,
            "Preco_Unitario_5D": None,
        }

        # 2. Extração Semântica (Busca dinâmica pelas chaves; o primeiro valor encontrado é mantido)
        for pset_name, props in psets.items():
            for chave, valor in props.items():
                chave_lower = chave.lower()

                # 4D: Planejamento / Cronograma
                # Só aceita valores texto, para não confundir uma data com p.ex. "End Offset" = 0.5
                campo_data = classificar_data(chave_lower)
                if campo_data and isinstance(valor, str):
                    if campos[campo_data] is None:
                        campos[campo_data] = valor

                # 3D: Dimensões (geralmente em QuantitySets como Qto_WallBaseQuantities)
                elif 'volume' in chave_lower:
                    if campos["Volume_m3"] is None:
                        campos["Volume_m3"] = valor
                elif 'area' in chave_lower:
                    if campos["Area_m2"] is None:
                        campos["Area_m2"] = valor

                # 5D: Custos
                elif any(k in chave_lower for k in ['cost', 'price', 'custo', 'preco', 'preço']):
                    if campos["Preco_Unitario_5D"] is None:
                        campos["Preco_Unitario_5D"] = valor

        dados_extraidos.append({
            "GlobalID": elem.GlobalId,
            "Nome": elem.Name or "Sem Nome",
            "Tipo_IFC": elem.is_a(),
            **campos,
        })

    return dados_extraidos

# --- Execução Principal ---
if __name__ == "__main__":
    caminho_ifc = PASTA_SCRIPT.parent / "Modelos" / "RSP-116RJ-218-226-ACA-EXE-MB-L2-019-R01-2X3.ifc"  # Substitua pelo caminho do seu arquivo .ifc
    pasta_saida = PASTA_SCRIPT / "resultados_dados_semanticos"
    pasta_saida.mkdir(parents=True, exist_ok=True)

    # Executa a extração
    resultado = extrair_dados_semanticos(caminho_ifc)

    # Salva os resultados em formato JSON estruturado
    with open(pasta_saida / "dados_semanticos_bim.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)

    # Salva também em uma tabela CSV
    df = pd.DataFrame(resultado)
    df.to_csv(pasta_saida / "dados_semanticos_bim.csv", index=False)

    print(f"Extração semântica concluída com sucesso! Arquivos JSON e CSV gerados em: {pasta_saida}")
