PYTHON ?= python
STREAMLIT ?= streamlit
CONFIG_DIR ?= config

.PHONY: validate prepare-dem preprocess-dem flow streams watershed morphometry lineaments flood-factors flood-index rank maps report all dashboard

validate:
	$(PYTHON) scripts/01_validate_project_inputs.py --config-dir $(CONFIG_DIR)

prepare-dem:
	$(PYTHON) scripts/02_prepare_study_area_and_dem.py --config-dir $(CONFIG_DIR)

preprocess-dem:
	$(PYTHON) scripts/03_preprocess_dem.py --config-dir $(CONFIG_DIR)

flow:
	$(PYTHON) scripts/04_generate_flow_direction_and_accumulation.py --config-dir $(CONFIG_DIR)

streams:
	$(PYTHON) scripts/05_extract_stream_network.py --config-dir $(CONFIG_DIR)

watershed:
	$(PYTHON) scripts/06_delineate_watershed_and_subbasins.py --config-dir $(CONFIG_DIR)

morphometry:
	$(PYTHON) scripts/07_compute_morphometric_parameters.py --config-dir $(CONFIG_DIR)

lineaments:
	$(PYTHON) scripts/08_lineament_drainage_analysis.py --config-dir $(CONFIG_DIR)

flood-factors:
	$(PYTHON) scripts/09_prepare_flood_hazard_factors.py --config-dir $(CONFIG_DIR)

flood-index:
	$(PYTHON) scripts/10_compute_flood_hazard_index.py --config-dir $(CONFIG_DIR)

rank:
	$(PYTHON) scripts/11_rank_subbasins.py --config-dir $(CONFIG_DIR)

maps:
	$(PYTHON) scripts/12_generate_maps_charts_and_summary_outputs.py --config-dir $(CONFIG_DIR)

report:
	$(PYTHON) scripts/13_generate_report_assets.py --config-dir $(CONFIG_DIR)

all: validate prepare-dem preprocess-dem flow streams watershed morphometry lineaments flood-factors flood-index rank maps report

dashboard:
	$(STREAMLIT) run app/streamlit_app.py

