

import pandas as pd
import xarray as xr
import numpy as np
from multiprocessing import Pool, cpu_count
import os
import argparse


model_input_dir = "./Resource/"
climate_scenario = 'rcp45hotter'  # 'historic' or 'rcp85hotter' or 'rcp85colder'
iso_region = 'ISONE'
top_n=8
# Climate scenario selection
if climate_scenario == 'historic':
    full_year_list = list(range(2001, 2020))  # Historical period: 2001-2019
else:
    full_year_list = list(range(2020, 2060))  # Future period: 2020-2029

output_dir=f'./Resource/'



def process_year(args):
    """Process capacity factor data for a single year"""
    year, technology_type,filesuffix, countylist,location_data, iso_region,climate_scenario = args
    print(f"Processing {technology_type} capacity factors for year {year}...")
    CF = xr.open_dataset(filesuffix + str(year) + '.nc')['capacity_factor']
    CF = CF.stack(z=('y', 'x')).dropna(dim='z')
    dates = CF['Time'].values.astype(str)
        
    try:
        base_dates = dates.astype(float).astype(int)  # e.g., 20200101
        frac_days = dates.astype(float) - base_dates  # e.g., 0.04166667
        base_datetimes = pd.to_datetime(base_dates, format="%Y%m%d")
        final_times = base_datetimes + pd.to_timedelta(frac_days, unit='D')
        final_times = final_times.round('h')
    except:
        final_times = pd.to_datetime(dates)
    CF['Time'] = final_times
    CF_df = CF.to_dataframe()[['capacity_factor', 'lat', 'lon']].reset_index()
    CF_df=CF_df.set_index(['lat','lon'])

    #if year==full_year_list[0]: 
    #    Vre_table=pd.DataFrame({'name':[], 'mask':[],'lat':[],'lon':[],'loc_index':[],'FIPS':[]})
    data_to_combine = {}

    for zone_id in countylist.index:
        county_row = countylist.loc[zone_id]
        num_selected_locations = county_row['Selected_Locations']
        county_id = county_row['FIPS']
        selected_locations = location_data[location_data['FIPS'] == county_id]
        if (len(selected_locations) != num_selected_locations):
            print(f"Warning: Number of selected locations ({len(selected_locations)}) does not match summary ({num_selected_locations}) for county {county_id}")
        selected_locations=selected_locations.sort_values(by='loc_index').reset_index(drop=True)

        for i,location in selected_locations.iterrows():
            col_name = f"{county_id}_{technology_type}_{i}"
            try:
                capacity_factors = CF_df.loc[(location['lat'], location['lon']),'capacity_factor'].values
                data_to_combine[col_name] = capacity_factors
            except KeyError:
                print(f"Coordinates (lat: {location.lat}, lon: {location.lon}) not found.")
            # vre_item=pd.DataFrame({'name': f"{county_id}_{technology_type}_{loc_index}", 
            #                             'mask': location.mask*144,
            #                             'lat': location.lat,
            #                             'lon': location.lon,
            #                             'loc_index': int(location.loc_index),
            #                             'FIPS': county_id}, index=[0])
            # Vre_table=pd.concat([Vre_table,vre_item],ignore_index=True)
        if num_selected_locations<top_n:
            for i in range(num_selected_locations, top_n):
                data_to_combine[f"{county_id}_{technology_type}_{i}"] = 0
                # vre_item=pd.DataFrame({'name': f"{county_id}_{technology_type}_{i}", 
                #                             'mask': 0,
                #                             'lat': np.nan,
                #                             'lon': np.nan,
                #                             'loc_index': int(i),
                #                             'FIPS': county_id}, index=[0])
                # Vre_table=pd.concat([Vre_table,vre_item],ignore_index=True)  
    
    power_DF = pd.DataFrame(data_to_combine)
    power_DF.index.name='Time'
    power_DF.to_csv(f'./Resource/{iso_region}/cf_{technology_type}/{climate_scenario}/{year}.csv')
    # if year==full_year_list[0]:
    #     Vre_table.to_csv(f'./Resource/{iso_region}/cf_{technology_type}/Loc_table.csv')

# =============================================================================
# DATA LOADING AND INITIALIZATION
# ============================================================================
countylist = pd.read_csv(
    f"{model_input_dir}/candidates_{iso_region}_summary.csv", 
    dtype={'FIPS': int},
)
countylist['Zone'] = np.arange(1, len(countylist) + 1).tolist()
countylist = countylist.set_index(['Zone'])

# Load detailed location data for renewable energy sites
location_data = pd.read_csv(
    f"{model_input_dir}/candidates_{iso_region}_by_county.csv", 
    dtype={'FIPS': int}
)

# =============================================================================
# MAIN PROCESSING LOOP: COUNTY-LEVEL RESOURCE SYNTHESIS
# =============================================================================
for technology_type in ['wind','solar']:
    filesuffix = "/orcd/nese/mhowland/001/lyqiu/GODEEP/data/%s/%s/%s/%s_gen_cf_" % ( climate_scenario , technology_type, iso_region, technology_type)
    args_list=[(year, technology_type,filesuffix, countylist,location_data, iso_region,climate_scenario) for year in full_year_list]
    # Process years in parallel
    n_processes = 10
    print(f"Using {n_processes} processes")
    with Pool(processes=n_processes) as pool:
        pool.map(process_year, args_list)
    