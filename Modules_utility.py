
import pandas as pd
import numpy as np
import os
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.crs import PlateCarree
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from cartopy.feature import ShapelyFeature, OCEAN, LAKES
from cartopy.mpl.patch import geos_to_path
from cartopy.io.shapereader import Reader as ShapeReader, natural_earth
from cartopy.mpl.gridliner import LongitudeFormatter, LatitudeFormatter
import geocat.viz as gv



import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm,TwoSlopeNorm
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.lines as mlines

# Custom rounding: 4 digits for <1, 2 digits otherwise
def smart_round(x):
    return round(x, 4) if x < 1 else round(x, 2)

def calculate_wacc(
    debt_ratio,
    cost_of_debt,
    equity_ratio,
    cost_of_equity,
    tax_rate,
    inflation_rate=None
):
    """
    Calculate nominal and (optionally) real WACC.

    Parameters:
    - debt_ratio: float (e.g., 0.6 for 60%)
    - cost_of_debt: float (e.g., 0.05 for 5%)
    - equity_ratio: float (e.g., 0.4 for 40%)
    - cost_of_equity: float (e.g., 0.1 for 10%)
    - tax_rate: float (e.g., 0.25 for 25%)
    - inflation_rate: float or None (e.g., 0.02 for 2%). If None, real WACC not calculated.

    Returns:
    - Dictionary with nominal WACC and (optionally) real WACC
    """
    # Nominal WACC
    wacc_nominal = (
        debt_ratio * cost_of_debt * (1 - tax_rate) +
        equity_ratio * cost_of_equity
    )

    result = {'wacc_nominal': wacc_nominal}

    if inflation_rate is not None:
        # Fisher equation for real WACC
        wacc_real = (1 + wacc_nominal) / (1 + inflation_rate) - 1
        result['wacc_real'] = wacc_real

    return result


def CRF(WACC, Lifetime):
    return (WACC * (1 + WACC)**Lifetime) / ((1 + WACC)**Lifetime - 1)


def capacity_ratio(t, k, midpoint):
    return 1 / (1 + np.exp(-k * (t - midpoint)))


def calculate_LCOE(CAPEX, OPEX, lifetime, WACC,MEAN_CF):
    """
    Calculate the Levelized Cost of Energy (LCOE).
    
    Parameters:
    - CAPEX: Capital Expenditure
    - OPEX: Operational Expenditure
    - lifetime: Project lifetime in years
    - WACC: Weighted Average Cost of Capital
    - MEAN_CF: Mean Capacity Factor
    
    Returns:
    - LCOE in $/MWh
    """
    crf=CRF(WACC, lifetime)
    
    total_cost = crf*CAPEX + OPEX 
    lcoe = total_cost / (MEAN_CF * 8760 )
    return lcoe

def virtual_potential_to_actual_temp(theta_v, p_Pa, p0_Pa=101325):
    """
    Convert virtual potential temperature to actual temperature.
    
    Parameters:
    - theta_v: virtual potential temperature in Celsius
    - p_Pa: actual pressure in Pa
    - p0_Pa: reference pressure in Pa (default: 101325 Pa = 1013.25 hPa)
    
    Returns:
    - actual temperature in Celsius
    """
    # Convert to Kelvin for calculations
    theta_v_K = theta_v + 273.15
    
    # Convert virtual potential temperature to actual temperature
    # T = theta_v * (p/p0)^(R/cp)
    # where R/cp ≈ 0.286 for dry air
    T_K = theta_v_K * (p_Pa / p0_Pa) ** 0.286
    
    # Convert back to Celsius
    return T_K - 273.15

def air_density(p_Pa, t=None, rh=None, q=None, theta_v=None):
    """
    Calculate air density based on pressure, temperature, and humidity.
    
    Parameters:
    - p_Pa: pressure in Pa
    - t: temperature in Celsius (optional if theta_v provided)
    - rh: relative humidity in % (optional, use if q not provided)
    - q: specific humidity in kg/kg (optional, use if rh not provided)
    - theta_v: virtual potential temperature in Celsius (optional, use if t not provided)
    
    Returns:
    - air density in kg/m³
    """
    R_d = 287.05  # J/(kg·K), specific gas constant for dry air
    
    # Convert virtual potential temperature to actual temperature if needed
    if t is None and theta_v is not None:
        t = virtual_potential_to_actual_temp(theta_v, p_Pa)
    elif t is None and theta_v is None:
        raise ValueError("Either actual temperature (t) or virtual potential temperature (theta_v) must be provided")
    
    # Input validation
    if p_Pa.mean() < 5000:
        print('Pressure is too low, check if the pressure data is in Pa.')
    if t.mean() > 100:
        print('Temperature is too high, check if the temperature data is in Celsius.')
    
    # Convert relative humidity to specific humidity if needed
    if q is None and rh is not None:
        # Convert relative humidity to specific humidity
        # Saturation vapor pressure (Pa) - Tetens formula
        es = 610.94 * np.exp(17.625 * t / (t + 243.04))
        
        # Actual vapor pressure (Pa)
        e = (rh / 100.0) * es
        
        # Specific humidity (kg/kg)
        q = 0.622 * e / (p_Pa - 0.378 * e)
    elif q is None and rh is None:
        raise ValueError("Either relative humidity (rh) or specific humidity (q) must be provided")
    
    return p_Pa / (R_d * (t + 273.15) * (1 + 0.61 * q))


    
    # 2. Get temperature - use direct measurement if available, otherwise interpolate
    if target_height in temp_heights:
        temperature = data[f'air temperature at {target_height}m (C)']
    else:
        # Linear interpolation with height
        lower_temps = [h for h in temp_heights if h < target_height]
        upper_temps = [h for h in temp_heights if h > target_height]
        
        if lower_temps and upper_temps:
            h1, h2 = max(lower_temps), min(upper_temps)
            t1 = data[f'air temperature at {h1}m (C)']
            t2 = data[f'air temperature at {h2}m (C)']
            # Linear interpolation
            temperature = t1 + (t2 - t1) * (target_height - h1) / (h2 - h1)
        else:
            # Use nearest available temperature
            ref_height = min(temp_heights, key=lambda x: abs(x - target_height))
            temperature = data[f'air temperature at {ref_height}m (C)']
    
    # 3. Get pressure - interpolate from available pressures
    if target_height == 0:
        pressure = data['surface air pressure (Pa)']
    elif target_height in [100, 200, 500]:
        pressure = data[f'air pressure at {target_height}m (Pa)']
    else:
        # Interpolate pressure using barometric formula
        p_surface = data['surface air pressure (Pa)']
        # Use standard atmosphere lapse rate for pressure estimation
        # p = p0 * exp(-g*M*h/(R*T))
        # Simplified: p ≈ p0 * (1 - 0.0065*h/T0)^(g*M/(R*0.0065))
        T0 = data['air temperature at 2m (C)'] + 273.15  # Surface temp in K
        pressure = p_surface * (1 - 0.0065 * target_height / T0) ** 5.26
    
    # 4. Calculate air density using surface relative humidity (assumption for building heights)
    rh_surface = data['relative humidity at 2m (%)']
    density = air_density(pressure, t=temperature, rh=rh_surface)
    
    return {
        'height': target_height,
        'wind_speed': wind_speed,
        'temperature': temperature, 
        'pressure': pressure,
        'air_density': density,
        'relative_humidity': rh_surface
    }


def setupmapbg(ax,ISO):


    if ISO=='ISONE':
        latmin=40.2;latmax=47.8;lonmin=-74;lonmax=-66.8
        latticks=[42,46]
        lonticks=[-72,-68]
    elif ISO=='ERCOT':
        latmin=25.5;latmax=37;lonmin=-107;lonmax=-93
        latticks=[26,30,34]
        lonticks=[-106,-102,-98,-94]
    elif ISO=='CAISO':
        latmin=32;latmax=42;lonmin=-125;lonmax=-114
        latticks=[34,38]
        lonticks=[-124,-120,-116]
    ax.set_extent([lonmin, lonmax, latmin, latmax])
    # ax.add_feature(cfeature.NaturalEarthFeature(category='cultural', name='admin_1_states_provinces',
    #                                             scale='10m', facecolor='none', edgecolor='black',
    #                                             linewidth=0.5, zorder=5))
    ax.coastlines(linewidth=0.3, zorder=1)
    gv.set_axes_limits_and_ticks(ax, xticks=lonticks, yticks=latticks)
    ax.yaxis.set_major_formatter(LatitudeFormatter(degree_symbol=''))
    ax.xaxis.set_major_formatter(LatitudeFormatter(degree_symbol=''))
    for axis in ['top', 'bottom', 'left', 'right']:
        ax.spines[axis].set_linewidth(2)

def setup_map_panel_ticks(ax, ir, ic, nr, xlabel, ylabel):
    ax.tick_params(axis='both', right=False, top=False, left=True, bottom=True, length=2,
                   pad=0.5, labelsize=plt.rcParams['xtick.labelsize']-1.5)
    ax.yaxis.set_ticklabels([])
    ax.xaxis.set_ticklabels([])
    if ir == nr-1:
        gv.add_lat_lon_ticklabels(ax)
        ax.yaxis.set_major_formatter(LatitudeFormatter(degree_symbol=''))
        ax.xaxis.set_major_formatter(LongitudeFormatter(degree_symbol=''))
        if ic != 0:
            ax.yaxis.set_ticklabels([])
        ax.set_xlabel(xlabel)
    else:
        ax.xaxis.set_tick_params(top=False, labeltop=False)
    if ic == 0:
        gv.add_lat_lon_ticklabels(ax)
        ax.yaxis.set_major_formatter(LatitudeFormatter(degree_symbol=''))
        ax.xaxis.set_major_formatter(LongitudeFormatter(degree_symbol=''))
        if ir != nr-1:
            ax.xaxis.set_ticklabels([])
        ax.set_ylabel(ylabel)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=90, va='center')
    else:
        ax.yaxis.set_tick_params(right=False, labelright=False)

def setsubtitle(ax, title, ni=None, nrc=None, pad=plt.rcParams['axes.titlepad'], subt_fontsize=plt.rcParams['axes.titlesize'],fw='bold'):
    if ni == None:
        if nrc == None:
            ax.set_title(f'{title}', fontsize=subt_fontsize,
                         loc='left', pad=pad, va='center',fontweight=fw)
        else:
            ir = nrc[0]
            ic = nrc[1]
            nc = nrc[3]
            ni = ir*nc+ic
            ax.set_title(f'({string.ascii_lowercase[ni]}) {title}', 
                         fontsize=subt_fontsize, loc='left', pad=pad, va='center',fontweight=fw)
    else:
        ax.set_title(f'({string.ascii_lowercase[ni]}) {title}',
                      fontsize=subt_fontsize, loc='left', pad=pad, va='center',fontweight=fw)