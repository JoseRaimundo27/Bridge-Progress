import ifcopenshell
import ifcopenshell.util.element
import pandas as pd
import json

def extrair_dados_semanticos(ifc_file_path):
    # 1. Carregamento do arquivo IFC
    print(f"Carregando o arquivo: {ifc_file_path}...")
    model = ifcopenshell.open(ifc_file_path)
    
    # Filtrar apenas elementos físicos de construção (ignora eixos, espaços virtuais, etc.)
    elementos = model.by_type("IfcBuildingElement")
    print(f"Total de elementos físicos encontrados: {len(elementos)}")
    
    dados_extraidos = []
    
    for elem in elementos:
        global_id = elem.GlobalId
        nome = elem.Name or "Sem Nome"
        tipo = elem.is_a()
        
        # Pega todos os PropertySets e QuantitySets associados ao elemento
        psets = ifcopenshell.util.element.get_psets(elem)
        
        # Inicializa variáveis
        volume = None
        area = None
        data_inicio_planejado = None
        data_inicio_real= None
        data_fim_planejado = None
        data_fim_real = None
        preco_unitario = None
        
        # 2. Extração Semântica (Busca dinâmica pelas chaves)
        for pset_name, props in psets.items():
            for chave, valor in props.items():
                chave_lower = chave.lower()
                
                # 3D: Dimensões (geralmente em QuantitySets como Qto_WallBaseQuantities)
                if 'volume' in chave_lower and volume is None:
                    volume = valor
                elif 'area' in chave_lower and area is None:
                    area = valor
                
                # 4D: Planejamento / Cronograma
                elif any(k in chave_lower for k in ['start','Contained in Task Start (Planned)', 'inicio', 'schedule']) and data_inicio_planejado is None:
                    data_inicio_planejado = str(valor)
                elif any(k in chave_lower for k in ['finish', 'Contained in Task Start (Actual)', 'end (planned)', 'fim', 'termino']) and data_inicio_real is None:
                    data_inicio_real = str(valor)
                elif any(k in chave_lower for k in ['finish', 'Contained in Task End (Planned)', 'end (planned)', 'fim', 'termino']) and data_fim_planejado is None:
                    data_fim_planejado = str(valor)
                elif any(k in chave_lower for k in ['finish', 'Contained in Task End (Actual)', 'end (planned)', 'fim', 'termino']) and data_fim_real is None:
                    data_fim_real = str(valor)
                
                
                # 5D: Custos
                elif any(k in chave_lower for k in ['cost', 'price', 'custo', 'preco']) and preco_unitario is None:
                    preco_unitario = valor

        dados_extraidos.append({
            "GlobalID": global_id,
            "Nome": nome,
            "Tipo_IFC": tipo,
            "Volume_m3": volume,
            "Area_m2": area,
            "Data_Inicio_Planejado": data_inicio_planejado,
            "Data_Inicio_Real": data_inicio_real,
            "Data_Fim_Planejado": data_fim_planejado,
            "Data_Fim_Real": data_fim_real,
            "Preco_Unitario_5D": preco_unitario
        })

    return dados_extraidos

# --- Execução Principal ---
if __name__ == "__main__":
    caminho_ifc = "../Modelos/RSP-116RJ-218-226-ACA-EXE-MB-L2-019-R01-2X3.ifc"  # Substitua pelo caminho do seu arquivo .ifc
    
    # Executa a extração
    resultado = extrair_dados_semanticos(caminho_ifc)
    
    # Salva os resultados em formato JSON estruturado
    with open("./resultados_dados_semanticos/dados_semanticos_bim.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)
        
    # Salva também em uma tabela CSV
    df = pd.DataFrame(resultado)
    df.to_csv("./resultados_dados_semanticos/dados_semanticos_bim.csv", index=False)
    
    print("Extração semântica concluída com sucesso! Arquivos JSON e CSV gerados.")