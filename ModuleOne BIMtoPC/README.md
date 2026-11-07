# Module I: BIM to Point Cloud (BIMtoPC)

This module is responsible for processing the as-planned 4D model (in IFC format) and extracting the necessary data for progress monitoring. It converts the parametric BIM elements into two main outputs: semantic data and a synthetic point cloud.

## Methodology and Workflow

The processing follows a parallel workflow to ensure the full extraction of both geometry and metadata, as shown in the diagram below:

<img src="./docs/Modulo I.png">

### 1. Data Origin and Development Environment
- **Data Origin and Types:** The input data is a BIM model in the open standard **IFC** format (supporting IFC2x3, IFC4, and IFC4x3), containing the 3D geometry of the bridge, schedule metadata (4D - planned dates), and cost/quantity metadata (5D).
- **Environment and Libraries:** Development is done on Ubuntu 26.04 on WSL2 using **Python (3.12.3)**. Semantic processing and geometry reading rely on **IfcOpenShell**, while 3D mesh manipulation and point sampling are performed using **Open3D** and **NumPy**. Pipeline automation is orchestrated via **Make**.
- **Hardware:** 
  - CPU: Intel Core i7-12700KF — 12 cores (8 P-cores + 4 E-cores), 20 threads
  - GPU: NVIDIA GeForce RTX 3080
  - RAM: 64 GB 3200 MHz
  - Storage: 4 TB Seagate SkyHawk (ST4000VX013)

### 2. Procedures and Data Treatment
The processing follows a parallel workflow to guarantee the complete extraction of both geometry and metadata:
- **Coordinate Correction (UTM to Local):** Infrastructure models usually use georeferenced coordinates (UTM) with very high scalar values. To avoid floating-point precision loss in Open3D, the model is translated to a local origin (0,0,0) prior to sampling.
- **Parallel Semantic Extraction:** Reads the 4D and 5D properties (dates, costs, volumes) and maps them by the unique `GlobalId` of each element.
- **Cloud Generation (Poisson Disk Sampling):** The mesh of each physical element is isolated, converting parametric vertices and faces into a `TriangleMesh`. A synthetic point cloud (*as-planned*) is then generated using the **Poisson Disk** algorithm. The number of points generated per element is proportional to its surface area, ensuring a homogeneous spatial density for the entire structure, regardless of the size of the pieces. The union of all individual clouds forms the global cloud.

### 3. Evaluation and Performance Metrics
Since this module deals with deterministic extraction and geometric sampling (without involving AI), the performance and quality of the process are measured through:
- **Extraction Success Rate (Completeness):** The ratio between the number of elements with geometric representation in the IFC file and the number of elements successfully converted into point clouds (`.ply` files). The ideal is 100%, indicating zero failures in mesh translation.
- **Density Homogeneity (points/m²):** Evaluates whether the *Poisson Disk* sampling maintained the desired constant density across different elements (e.g., density variation between a large-volume pier and a small bearing).
- **Geometric Fidelity:** The error distance (e.g., *Point-to-Mesh distance*) between the points of the generated cloud and the original 3D mesh surface, ensuring that the discretization did not alter the shape of the pieces.
- **Processing Time (Throughput):** The computational time in seconds required to parse the entire IFC model, extract semantic information, and generate the global as-planned cloud.

## Script Description (`Python/`)

### Main Processing
- **`UTMtoLocalCoordinates.py`**: Translates the IFC model from global coordinates (UTM) to local coordinates. It must be the first step in the geometric processing.
- **`dados_semanticos.py`**: Reads the IFC model and extracts the properties of each element (GlobalId, planned dates, unit cost, etc.), saving the results in the `resultados_dados_semanticos/` folder.
- **`geometriaEnuvem.py`**: Executes the **Geometric Extraction** and **Cloud Generation**. It extracts the individual geometry of each piece by converting the parametric information (vertices and faces) from IfcOpenShell into 3D meshes (TriangleMesh) for Open3D. It then applies *Poisson Disk* sampling to generate the element's cloud, saves it in `resultados_geometricos/` by its `GlobalId`, and finally consolidates the complete cloud of the structure in `resultado_nuvem_global/`.

### Utilities and Visualization (Optional)
- **`ifc_utils.py`**: A script containing reusable auxiliary functions for manipulating and reading IFC files.
- **`visualizeIFC.py`**: A 3D viewer to inspect the original input model (`Modelos/*.ifc`).
- **`visualizePLY.py`**: A viewer to inspect the generated point clouds (e.g., validating the cloud in `resultado_nuvem_global/`).

## How to Run and Test

### 1. Preparation
Make sure your `.ifc` model is inside the `Modelos/` folder.

### 2. Automated Processing (Recommended)
The easiest way to run the full pipeline of this module is by using the Makefile in the root of the repository:
```bash
cd ../../  # Return to the root of the project
make m1
[⬅ Back to the main README](../README.md)
