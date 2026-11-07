# Module I: BIM to Point Cloud (BIMtoPC)

Este módulo é responsável por processar o modelo as-planned 4d(em formato IFC) e extrair os dados necessários para o monitoramento de progresso. Ele converte os elementos paramétricos do BIM em duas saídas principais: dados semânticos  e uma nuvem de pontos sintética.

## Metodologia e Fluxo de Trabalho

O processamento segue um fluxo paralelo para garantir a extração íntegra tanto da geometria quanto dos metadados, conforme o diagrama abaixo:

<img src="./docs/Modulo I.png">


   ### 1. Origem dos Dados e Ambiente de Desenvolvimento
- **Origem e Tipos de Dados:** O dado de entrada é um modelo BIM no formato padrão aberto **IFC** (suportando IFC2x3, IFC4 e IFC4x3), contendo a geometria 3D da ponte, metadados de cronograma (4D - datas planejadas) e de custo/quantidades (5D).
- **Ambiente e Bibliotecas:** O desenvolvimento é feito em Ubuntu 26.04 on WSL2 **Python (3.12.3)**. O processamento semântico e a leitura de geometria dependem do **IfcOpenShell**, enquanto a manipulação das malhas 3D e a amostragem de pontos são realizadas utilizando o **Open3D** e **NumPy**. A automação do pipeline é orquestrada via **Make**.
CPU: Intel Core i7-12700KF — 12 núcleos (8 P-cores + 4 E-cores), 20 threads.
GPU: NVIDIA GeForce RTX 3080.
RAM: 64 GB 3200 MHZ.
Disco: Seagate SkyHawk de 4 TB (ST4000VX013).

### 2. Procedimentos e Tratamento dos Dados
O processamento segue um fluxo paralelo para garantir a extração íntegra tanto da geometria quanto dos metadados:
- **Correção de Coordenadas (UTM to Local):** Modelos de infraestrutura costumam usar coordenadas georreferenciadas (UTM) com valores escalares muito altos. Para evitar perdas de precisão de ponto flutuante (*floating-point precision loss*) no Open3D, o modelo é transladado para uma origem local (0,0,0) antes da amostragem.
- **Extração Semântica Paralela:** Leitura das propriedades 4D e 5D (datas, custos, volumes) e mapeamento pelo `GlobalId` único de cada elemento.
- **Geração da Nuvem (Poisson Disk Sampling):** Isola-se a malha (mesh) de cada elemento físico, convertendo vértices e faces paramétricas em `TriangleMesh`. Em seguida, gera-se uma nuvem de pontos sintética (*as-planned*) por meio do algoritmo de **Poisson Disk**. A quantidade de pontos gerada por elemento é proporcional à sua área superficial, garantindo uma densidade espacial homogênea para toda a estrutura, independente do tamanho das peças. A união de todas as nuvens individuais compõe a nuvem global.

### 3. Métricas de Avaliação e Desempenho
Como este módulo lida com extração determinística e amostragem geométrica (não envolvendo IA), o desempenho e a qualidade do processo são medidos através de:

- **Taxa de Sucesso da Extração (Completeness):** Proporção entre o número de elementos com representação geométrica no arquivo IFC e o número de elementos convertidos com sucesso em nuvens de pontos (arquivos `.ply`). O ideal é 100%, indicando zero falhas na tradução de malhas.
- **Homogeneidade da Densidade (pontos/m²):** Avalia se a amostragem do *Poisson Disk* manteve a densidade desejada constante ao longo de diferentes elementos (ex: variação da densidade entre um pilar de grande volume e um aparelho de apoio pequeno).
- **Fidelidade Geométrica:** Distância de erro (ex: *Point-to-Mesh distance*) entre os pontos da nuvem gerada e a superfície da malha 3D original, garantindo que a discretização não alterou o formato das peças.
- **Tempo de Processamento (Throughput):** Tempo computacional em segundos exigido para analisar o modelo IFC completo, extrair as informações semânticas e gerar a nuvem global as-planned.

## Descrição dos Scripts (`Python/`)

### Processamento Principal
- **`UTMtoLocalCoordinates.py`**: Translada o modelo IFC de coordenadas globais (UTM) para coordenadas locais. Deve ser o primeiro passo no processamento geométrico.
- **`dados_semanticos.py`**: Lê o modelo IFC e extrai as propriedades de cada elemento (GlobalId, datas planejadas, custo unitário, etc.), salvando os resultados na pasta `resultados_dados_semanticos/`.
- **`geometriaEnuvem.py`**: Executa a **Extração Geométrica** e a **Geração da Nuvem**. Ele extrai a geometria individual de cada peça convertendo as informações paramétricas (vértices e faces) do IfcOpenShell em malhas 3D (TriangleMesh) para o Open3D. Em seguida, aplica a amostragem de *Poisson Disk* para gerar a nuvem do elemento, salva em `resultados_geometricos/` pelo `GlobalId`, e por fim consolida a nuvem completa da obra em `resultado_nuvem_global/`.

### Utilitários e Visualização (Opcionais)
- **`ifc_utils.py`**: Script contendo funções auxiliares reutilizáveis para manipulação e leitura de arquivos IFC.
- **`visualizeIFC.py`**: Visualizador 3D para inspecionar o modelo de entrada original (`Modelos/*.ifc`).
- **`visualizePLY.py`**: Visualizador para inspecionar as nuvens de pontos geradas (ex: validar a nuvem em `resultado_nuvem_global/`).

## Como Executar e Testar

### 1. Preparação
Certifique-se de que o seu modelo `.ifc` está dentro da pasta `Modelos/`.

### 2. Processamento automatizado (Recomendado)
A forma mais fácil de rodar o pipeline completo deste módulo é utilizando o Makefile na raiz do repositório:
```bash
cd ../../  # Volte para a raiz do projeto
make m1`
```
[⬅ Voltar para o README principal](../README.md)
