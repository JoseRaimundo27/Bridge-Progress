# Bridge-Progress

Automated construction progress monitoring for **bridges** with a **Scan-vs-BIM** approach. The as-built point cloud of the bridge is compared with the as-planned 5D BIM model (IFC) to determine, element by element, whether the work is ahead of schedule, on schedule, pending or behind schedule, and what this represents in cost.

The method is based on:

> K. Tang and W. Shi (2026). _RandLA-Net-Assisted Scan-vs-BIM Framework with Adaptive Parameter Optimization for Construction Progress Monitoring_. J. Comput. Civ. Eng. 40(4): 04026034. DOI: [10.1061/JCCEE5.CPENG-6962](https://doi.org/10.1061/JCCEE5.CPENG-6962)

## How it works

```
 5D BIM (IFC) ──► I. BIM parsing ──► semantic data (3D/4D/5D) + geometry per element + synthetic point cloud
                                                                                        │
 As-built scan ──► II. AI-assisted preprocessing ──► RandLA-Net keeps only the bridge ──► OBBP-ICP registration
                                                                                        │
                   III. Element status recognition ◄────────────────────────────────────┘
                        coverage of each BIM element by the registered scan → built / not built
                                                                                        │
                   IV. Progress analytics ◄─────────────────────────────────────────────┘
                        scan date vs. planned date → schedule status, colour-coded model,
                        quantities and cost indicators (BCWS, ACWP, SV, SPI)
```

1. **BIM parsing**: reads the IFC model, extracts each element's `GlobalId`, quantities (volume, area), schedule dates and unit price, and samples its geometry into a synthetic as-planned point cloud.
2. **AI-assisted preprocessing**: [RandLA-Net](https://github.com/QingyongHu/RandLA-Net) semantic segmentation removes everything that is not the bridge (terrain, vegetation, cranes, equipment). The OBBP-ICP algorithm then aligns the cleaned scan with the as-planned cloud: it pre-aligns the oriented bounding boxes, refines with ICP and keeps the best candidate.
3. **Element status recognition**: for each BIM element, the scan points around it are projected onto grids, and their coverage of the element tells whether it is built.
4. **Progress analytics**: the element status is combined with the schedule and the unit prices to classify each element and to compute the progress deviation in quantity and cost.

## Requirements

- Linux, Python 3.10 – 3.12
- System packages: `sudo apt install python3-venv python3-full libusb-1.0-0`
- An NVIDIA GPU with CUDA to train RandLA-Net (the CPU works, but training is very slow)

## Installation

```bash
make install
```

This command creates a virtual environment in `.venv/`, installs `requirements.txt`, then installs Open3D and PyTorch: the CUDA builds (`open3d`, PyTorch cu126) when an NVIDIA GPU is detected, the CPU builds (`open3d-cpu`, PyTorch cpu) otherwise.

To choose another PyTorch build:

```bash
make install TORCH_INDEX=https://download.pytorch.org/whl/cu130
```

> The PyTorch version must match the version Open3D-ML was built against. If `import open3d.ml.torch` fails, its error message gives the expected version.

## Data

Data files are not versioned. Put them in these locations:

| Used by | Expected path |
|---|---|
| BIM parsing | `ModuleOne BIMtoPC/Modelos/*.ifc` (IFC2x3) |
| Segmentation | `ModuleTwo RandlaNET/DATASET/Ponte_Custom3D/{train,val}/*.ply` (fields `x y z red green blue label`) |
| Registration | `ModuleTwo Registration/AsBuilt/*.ply` and `ModuleTwo Registration/AsPlanned/*.ply` |

`ModuleTwo RandlaNET/Python/txt_ply.py` converts a `x y z r g b label` text file (for example a CloudCompare export) to this PLY format.

The input file names and paths are set at the top of each script.

## Usage

```bash
make help    # list the commands
make m1      # BIM parsing: semantic data + synthetic as-planned point cloud
make m2-1    # Segmentation: train RandLA-Net, then evaluate it
make m2-2    # Registration: OBBP-ICP
```

The Makefile uses `.venv/bin/python` by default. To use another interpreter: `make m1 PYTHON=python3`.

### Outputs

| Command | Output |
|---|---|
| `make m1` | `ModuleOne BIMtoPC/Python/resultados_dados_semanticos/` (JSON, CSV), `resultados_geometricos/<GlobalId>.ply`, `resultado_nuvem_global/modelo_as_planned_global.ply` |
| `make m2-1` | Checkpoints in `ModuleTwo RandlaNET/Python/logs_ponte/` |
| `make m2-2` | Registered scan displayed in an Open3D window, mean distance `D_avg` and transform matrix printed to the console |

### Other scripts

Run these from their own `Python/` folder:

- `ModuleOne BIMtoPC/Python/visualizeIFC.py`: view the IFC model
- `ModuleTwo RandlaNET/Python/view_ground_truth.py`: view the annotated ground truth
- `ModuleTwo RandlaNET/Python/view_ia_result.py`: segment a point cloud with the trained model and view the result

## References

- K. Tang, W. Shi (2026). _RandLA-Net-Assisted Scan-vs-BIM Framework with Adaptive Parameter Optimization for Construction Progress Monitoring_. J. Comput. Civ. Eng.
- Q. Hu et al. (2020). _RandLA-Net: Efficient Semantic Segmentation of Large-Scale Point Clouds_. CVPR.
- [Open3D-ML RandLA-Net documentation](https://www.open3d.org/docs/latest/python_api/open3d.ml.torch.models.RandLANet.html)
