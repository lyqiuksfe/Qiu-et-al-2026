# Qiu_et_al_2025

## Preprocess.ipynb
### 1. Network set-up
#### 1.1 Node: County level
- **64** counties in ISONE (excluding Dukes and Nantucket because they are isolated nodes) and **214** counties in ERCOT
- Use the city with most population in the county as the node center

**Output:** preprocess/Network/ISONE_county_list.csv

#### 1.2 Tranmission Lines: Aggreated from existing network

[Gituhb repo: Transmission Network Aggregator by Shen Wang](https://github.com/swang22/Transmission-Network-Aggregator)

    -> **159** lines in ISONE and **459** in ERCOT

**Output:** preprocess/Network/Transmission_Lines_ERCOT_existing.csv

### 2. Land-use filter
- 100-m Renewable siting ordinances with 50th percentile of zoning ordinance setbacks for wind (Lopez et al., 2023) aggregated to 12-km (keeping grid cell with at least 20% area available)   

    -> **895** candidates in ISONE and **2373** in ERCOT

2. For each county, get the locations with top 8 largest available area

    -> **321** candidates in ISONE and **1430** in ERCOT


### 3. Capacity Factor
- 12-km climate projections from [Bracken et al. 2023](https://doi.org/10.5281/zenodo.10214348) + Land-use filter

**Output:** preprocess/Resource/ISONE/cf_*

### 4. Demand
- Disaggregated [ISO demand projection](https://www.sciencedirect.com/science/article/abs/pii/S0306261924023316) to counties by county population

**Output:** preprocess/Resource/ISONE/demand/


## Overview
###
This module implements a spatially explicit renewable energy investment and dispatch optimization model at the county level. The model determines optimal renewable energy capacity investments and operational decisions to meet electricity demand while minimizing total system costs.

## Overview

The optimization model can operate in two modes:
- **Investment Optimization**: Determines optimal capacity investments for renewable energy, transmission, and storage
- **Dispatch Optimization**: Optimizes operational decisions for given capacity installations



### Input Data Requirements

1. **Renewable Energy Data**: Hourly capacity factors by location and technology
2. **Demand Data**: Hourly electricity demand by county
3. **Technology Parameters**: Cost and performance characteristics
4. **Geographic Data**: County boundaries and renewable resource areas


## Dependencies

**External Data Sources:**
- PNNL renewable energy capacity factors
- TELL electricity demand projections
- Technology cost databases (NREL ATB)



## Contact

For questions about this model implementation:
- Author: Liying Qiu (lyqiu@mit.edu)
- Spatially explicit renewable energy optimization