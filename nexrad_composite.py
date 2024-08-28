from datetime import datetime,timedelta
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
from xarray import open_dataset
from xarray.backends import NetCDF4DataStore
from siphon.catalog import TDSCatalog
from netCDF4 import Dataset
import metpy
from metpy.plots import USCOUNTIES

def extract_and_format_date_time(radar_ds):
    parts = radar_ds.split('_')
    date_str = parts[4]
    time_str = parts[5].split('.')[0]
    datetime_str = date_str + time_str
    dt = datetime.strptime(datetime_str, '%Y%m%d%H%M')
    formatted_datetime = dt.strftime('%Y-%m-%d %H%M UTC')
    return formatted_datetime

now = datetime.now()
year = now.year
month = now.month
daytime = now.day

url = 'https://thredds.ucar.edu/thredds/catalog/nexrad/composite/gini/dhr/1km/{}{}{}/catlog.xml'.format(year,str(month).zfill(2),str(daytime).zfill(2))

for i in range(0,11):
    radar_ds = TDSCatalog(url)
    radar_ds = radar_ds.datasets
    ncss = radar_ds[i].subset()
    query = ncss.query()
    query.accept('netcdf4')
    query.variables('Reflectivity')
    radar_data = ncss.get_data(query)
    radar_data = open_dataset(NetCDF4DataStore(radar_data))
    radar_data_ds = radar_data.metpy.parse_cf().set_coords(['x', 'y'])
    radar_latlon = radar_data_ds.metpy.assign_latitude_longitude()
    radar_ref = radar_latlon['Reflectivity'][0,:,:]
    radar_ref = np.ma.masked_where(radar_ref < 5, radar_ref)
    formatted_datetime = extract_and_format_date_time(radar_ds[i].name)
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.PlateCarree()})
    ax.set_extent([-91, -81, 40.5, 47.75])
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'))
    ax.add_feature(cfeature.STATES.with_scale('50m'))
    ax.add_feature(cfeature.BORDERS.with_scale('50m'))
    ax.add_feature(USCOUNTIES.with_scale('5m'), linewidth=0.25)
    ax.add_feature(cfeature.LAKES, zorder=1, color='#ecf9fd')
    ax.add_feature(cfeature.LAND, color='#fbf5e9')
    mesh = plt.pcolormesh(radar_latlon['longitude'], radar_latlon['latitude'], radar_ref, cmap=metpy.plots.ctables.registry.get_colortable('NWSStormClearReflectivity'), vmin=-25, vmax=80)
    cbar = plt.colorbar(mesh, ax=ax, orientation='vertical', label='dBZ', fraction=0.046, pad=0.04, shrink=0.80)
    cbar.set_ticks(np.arange(-25, 81, 10))
    plt.title('NEXRAD Composite Reflectivity {}'.format(formatted_datetime))
    plt.savefig('reflectivity/nexrad/z_{}.png'.format(i), dpi=450, bbox_inches='tight')
    #plt.show()
