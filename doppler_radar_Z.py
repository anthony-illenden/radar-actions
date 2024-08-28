from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import metpy
from siphon.cdmr import Dataset
from siphon.radarserver import get_radarserver_datasets, RadarServer
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from metpy.plots import USCOUNTIES

def raw_to_masked_float(var, data):
    if np.issubdtype(var.dtype, np.unsignedinteger):
        data = data & 255
    data = np.ma.array(data, mask=data==0)
    return data * var.scale_factor + var.add_offset

def polar_to_cartesian(az, rng):
    az_rad = np.deg2rad(az)[:, None]
    x = rng * np.sin(az_rad)
    y = rng * np.cos(az_rad)
    return x, y

ds = get_radarserver_datasets('http://thredds.ucar.edu/thredds/')
url = ds['NEXRAD Level II Radar from IDD'].follow().catalog_url
rs = RadarServer(url)

query = rs.query()
query.stations('KDTX').time_range(datetime.utcnow() - timedelta(hours=1), datetime.utcnow())

rs.validate_query(query)
catalog = rs.get_catalog(query)

count = 0
for ds_name in sorted(catalog.datasets):
    dataset_obj = catalog.datasets[ds_name]  
    print(ds_name)
    data = Dataset(dataset_obj.access_urls['CdmRemote'])
    dv = data.variables
    sweep = 0
    ref_var = dv['Reflectivity']
    ref_data = ref_var[sweep]
    rng = dv['distanceR'][:]
    az = dv['azimuthR'][sweep]
    ref_clean2 = raw_to_masked_float(ref_var, ref_data)
    x, y = polar_to_cartesian(az, rng)

    file_info = str(ds_name)
    parts = file_info.split('_')
    radar_site = parts[1]
    date_str = parts[2]
    time_str = parts[3].split('.')[0]
    datetime_str = date_str + time_str
    dt = datetime.strptime(datetime_str, "%Y%m%d%H%M")
    formatted_datetime = dt.strftime("%Y-%m-%d %H:%M")
    fig, ax = plt.subplots(1,1, figsize=(12, 10), subplot_kw={'projection': ccrs.LambertConformal(central_longitude=data.StationLongitude, central_latitude=data.StationLatitude)})
    ax.set_extent([-86.0, -82.0, 41.0, 45.0])
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=2)
    ax.add_feature(cfeature.STATES.with_scale('50m'))
    ax.add_feature(USCOUNTIES.with_scale('5m'), linewidth=0.25)
    ax.add_feature(cfeature.LAKES, zorder=1, color='#ecf9fd')
    ax.add_feature(cfeature.LAND, color='#fbf5e9')
    ax.plot(-83.47, 42.7, 'ro', markersize=5, transform=ccrs.PlateCarree(), zorder=2, color='black')
    plt.title('{} Base Reflectivity at {} UTC'.format(data.Station, formatted_datetime), loc='center')
    img = ax.pcolormesh(x, y, ref_clean2, cmap=metpy.plots.ctables.registry.get_colortable('NWSStormClearReflectivity'), vmin=-35, vmax=80, zorder=0)
    cbar = fig.colorbar(img, orientation='vertical', label='Reflectivity (dBZ)', fraction=0.046, pad=0.04)
    cbar.set_ticks(np.arange(-35, 81, 10))
    print(ref_clean2.max())
    plt.text(0.995, 0.975, 'Max dBZ: {}'.format(ref_clean2.max()), horizontalalignment='right', transform=ax.transAxes)
    plt.show()
    plt.savefig('reflectivity/kdtx/z_{}.png'.format(count), dpi=450, bbox_inches='tight')
    count += 1
