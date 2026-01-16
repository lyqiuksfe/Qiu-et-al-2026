
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
import string

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

def get_sig_stars(p):
    if p < 0.001:
        return '***'
    elif p < 0.01:
        return '**'
    elif p < 0.05:
        return '*'
    else:
        return ''

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

def get_date(df, datv='dat', tz_original='UTC', tz_to='UTC',getmeta=True):   
    try: 
        df['Date'] = pd.to_datetime(df[datv]).dt.tz_localize(tz_original).dt.tz_convert(tz_to)
    except:
        df['Date'] = pd.to_datetime(df[datv]).dt.tz_convert(tz_to)
    df['Year']=df['Date'].dt.year
    df['Month'] =df['Date'].dt.month
    df['Hour'] = df['Date'].dt.hour
    df['Day'] = df['Date'].dt.day
    df['Season'] = df['Month'].apply(get_season)
    dfa = df[(df['Month'] == 2) & (df['Day'] == 29)]
    df.loc[dfa.index,'Date'] = df.loc[dfa.index,'Date'] + pd.Timedelta(days=-1)
    # # use the newdate to replace the index in df
    # df.loc[dfa.index, 'Date'] = dfa['newdate']
    df = df.set_index('Date')  # Set index to 'Date'
    return df


def get_season(month):
    if 3 <= month <= 5:
        return 2
    elif 6 <= month <= 8:
        return 3
    elif 9 <= month <= 11:
        return 4
    else:
        return 1
        
def CRF(WACC, Lifetime):
    return (WACC * (1 + WACC)**Lifetime) / ((1 + WACC)**Lifetime - 1)


def capacity_ratio(t, k, midpoint):
    return 1 / (1 + np.exp(-k * (t - midpoint)))


def setupmapbg(ax,ISO):
    if ISO=='ISONE':
        latmin=40.6;latmax=47.8;lonmin=-74;lonmax=-66.5
        latticks=[42,46]
        lonticks=[-72,-68]
    elif ISO=='ERCOT':
        latmin=25.5;latmax=36.6;lonmin=-105.5;lonmax=-93.5
        latticks=[26,30,34]
        lonticks=[-106,-102,-98,-94]
    elif ISO=='CAISO':
        latmin=32;latmax=42;lonmin=-125;lonmax=-113.5
        latticks=[34,38]
        lonticks=[-124,-120,-116]
    ax.set_extent([lonmin, lonmax, latmin, latmax])
    #gv.set_axes_limits_and_ticks(ax, xticks=lonticks, yticks=latticks)
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
        #gv.add_lat_lon_ticklabels(ax)
        ax.yaxis.set_major_formatter(LatitudeFormatter(degree_symbol=''))
        ax.xaxis.set_major_formatter(LongitudeFormatter(degree_symbol=''))
        if ic != 0:
            ax.yaxis.set_ticklabels([])
        ax.set_xlabel(xlabel)
    else:
        ax.xaxis.set_tick_params(top=False, labeltop=False)
    if ic == 0:
        #gv.add_lat_lon_ticklabels(ax)
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