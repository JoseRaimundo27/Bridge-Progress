VENV := $(CURDIR)/.venv
PYTHON ?= $(VENV)/bin/python

# Open3D-ML 0.20 is built against PyTorch 2.13
OPEN3D_VERSION ?= 0.20.0
TORCH_VERSION ?= 2.13.*
# GPU NVIDIA -> CUDA, else CPU
ifneq ($(shell command -v nvidia-smi 2>/dev/null),)
OPEN3D_PKG ?= open3d
TORCH_INDEX ?= https://download.pytorch.org/whl/cu126
else
OPEN3D_PKG ?= open3d-cpu
TORCH_INDEX ?= https://download.pytorch.org/whl/cpu
endif

# Open3D display settings for WSL (auto-detected, force with WSL=1 or WSL=0)
WSL ?= $(if $(shell grep -qi microsoft /proc/version 2>/dev/null && echo yes),1,0)
ifeq ($(WSL),1)
export XDG_SESSION_TYPE := x11
export GDK_BACKEND := x11
export LIBGL_ALWAYS_SOFTWARE := 1
endif

.PHONY: help install m1 m2-1 m2-2

help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'

install: ## Create .venv and install the dependencies
	@ldconfig -p | grep -q libusb-1.0 || { echo "Missing system library: run 'sudo apt install libusb-1.0-0'"; exit 1; }
	python3 -m venv "$(VENV)"
	"$(VENV)/bin/pip" install --upgrade pip
	"$(VENV)/bin/pip" install --resume-retries 20 -r requirements.txt
	"$(VENV)/bin/pip" install --resume-retries 20 "$(OPEN3D_PKG)[ml]==$(OPEN3D_VERSION)"
	"$(VENV)/bin/pip" install --resume-retries 20 "torch==$(TORCH_VERSION)" --index-url $(TORCH_INDEX)
	"$(VENV)/bin/python" -c "import open3d.ml.torch" && echo "Installation OK"

m1: ## Module 1 BIMtoPC
	cd "ModuleOne BIMtoPC/Python" && \
		"$(PYTHON)" dados_semanticos.py && "$(PYTHON)" geometriaEnuvem.py

m2-1: ## Module 2 RandLA-Net
	cd "ModuleTwo RandlaNET/Python" && "$(PYTHON)" train_ponte.py && "$(PYTHON)" test_ponte.py

m2-2: ## Module 2 Registration
	cd "ModuleTwo Registration/Python" && "$(PYTHON)" legacy/obbp_icp_v0.py
