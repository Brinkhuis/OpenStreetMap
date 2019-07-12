#%%
import numpy as np
import pandas as pd
import geopandas as gpd
import folium
import matplotlib.pyplot as plt
import requests
import json
import zipfile
from shapely.geometry import Point

#%%
def get_data(area, key, value):
    url = "http://overpass-api.de/api/interpreter"
    query ="""
    [out:json];
    area["ISO3166-1"="{0}"][admin_level=2];
    (node["{1}"="{2}"](area);
     way["{1}"="{2}"](area);
     rel["{1}"="{2}"](area);
    );
    out center;
    """.format(area, key, value)
    response = requests.get(url, params={'data': query})
    return response.json()

#%%
def get_coords(data):
    coords = []
    for element in data['elements']:
        if element['type'] == 'node':
            lon = element['lon']
            lat = element['lat']
            coords.append((lon, lat))
        elif 'center' in element:
            lon = element['center']['lon']
            lat = element['center']['lat']
            coords.append((lon, lat))
    return coords

#%%
url = 'https://www.imergis.nl/gpkg/2019_voorlopige_bestuurlijke_grenzen_imergis_gpkg.zip'
r = requests.get(url)
with open(url.split('/')[-1], 'wb') as file:
    file.write(r.content)

#%%
zip_ref = zipfile.ZipFile(url.split('/')[-1], 'r')
zip_ref.extractall()
zip_ref.close()

#%%
municipality = gpd.read_file('2019_gemeentegrenzen_kustlijn.gpkg')

#%%
area  = 'NL'
key   = 'amenity'
value = 'post_box'

#%%
data = get_data(area, key, value)
coords = get_coords(data)
coords = [c for c in coords if c[0] > 3] # drop results Netherlands Antilles
print(len(coords), f'data points found for \'{value}\'.')

#%%
geodata = pd.DataFrame(coords, columns=['lon', 'lat'])
geodata['geometry'] = geodata.apply(lambda g: Point((g.lon, g.lat)), axis=1)
geodata = gpd.GeoDataFrame(geodata, crs={'init': 'epsg:4326'}, geometry=geodata.geometry)
geodata.geometry = geodata.geometry.to_crs(municipality.crs)

#%%
f, ax = plt.subplots(figsize=(12, 12))
municipality.plot(ax=ax, color='white', edgecolor='darkgrey', linewidth=1)
geodata.plot(ax=ax, markersize=20, c='Royalblue', alpha=0.3)
plt.title(value, fontsize=20)
plt.axis('off')
plt.show()

#%%
counts = gpd.sjoin(municipality, geodata, how='inner', op='intersects')\
.groupby(by='gemeentenaam').size().to_frame('count').reset_index()
counts = pd.merge(municipality, counts, how='left', on='gemeentenaam').fillna(0)
counts['count'] = counts['count'].astype(int)

#%%
f, ax = plt.subplots(1, figsize=(12, 12))
counts.plot(ax=ax, column='count', cmap='tab20b', edgecolor='lightgrey', linewidth=0.3, legend=True)
plt.title(value, fontsize=20)
plt.axis('off')
plt.show()

#%%
m = folium.Map(location = [52.552, 5.150], zoom_start = 8)
folium.Choropleth(
    geo_data = counts,
    name = 'geometry',
    data = counts,
    columns = ['gemeentenaam', 'count'],
    key_on = 'feature.properties.gemeentenaam',
    fill_color = 'BuPu', # for valid fill_colors, visit http://colorbrewer2.org
    fill_opacity = 0.7,
    line_opacity = 0.7,
    legend_name = value,
    reset = True).add_to(m)
m.save('map.html')
