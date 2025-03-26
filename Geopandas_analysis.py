import geopandas as gpd
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

#all data -> https://drive.google.com/drive/folders/1zzZI8rDDN3fdiPGyuFzBGIg4o35peHQt?usp=drive_link
traffic = gpd.read_file('shp_data/traffic/traffic_data/traffic_filtered_shapefile.shp')
arrests = gpd.read_file('shp_data/arrests/arrests_data/arrests_filtered_shapefile.shp')
noise_complain = gpd.read_file('shp_data/noise/noise_complaints.shp')
air_emmisions = gpd.read_file('shp_data/air/fixed_air_pollution.shp')

    # positive aspects
schools = gpd.read_file("data/nyc/SchoolPoints_APS_2024_08_28 (1)/SchoolPoints_APS_2024_08_28.shp")
subways = gpd.read_file("data/nyc/nyc_subway_entrances/nyc_subway_entrances.shp")
bike_paths = gpd.read_file("data/nyc/New York City Bike Routes_20241223.geojson")
parks = gpd.read_file("data/nyc/Parks Properties_20241223.geojson")
sport = gpd.read_file("shp_data/sport/sport.shp")
culutral_places = gpd.read_file("shp_data/cultural/cultural_places.shp")

    # dzielnice
neighborhoods = gpd.read_file("https://raw.githubusercontent.com/HodgesWardElliott/custom-nyc-neighborhoods/refs/heads/master/custom-pedia-cities-nyc-Mar2018.geojson")




# region to_crs
traffic = traffic.to_crs("EPSG:3857")
arrests = arrests.to_crs("EPSG:3857")
noise_complain = noise_complain.to_crs("EPSG:3857")
air_emmisions = air_emmisions.to_crs("EPSG: 3857")
air_emmisions.rename(columns={'sum_ozone_': 'sum_ozone', 'aa_nitroge': 'sum_nitrogen', 'aa_nitric_': 'sum_nitric', 'aa_black_c':'sum_black_carbon'}, inplace=True)



schools = schools.to_crs("EPSG:3857")
subways = subways.to_crs("EPSG:3857")
bike_paths = bike_paths.to_crs("EPSG:3857")
parks = parks.to_crs("EPSG:3857")
sport = sport.to_crs("EPSG:3857")
culutral_places = culutral_places.to_crs("EPSG:3857")

neighborhoods = neighborhoods.to_crs("EPSG:3857")

# endregion

def analyze_neighborhood_postive_aspects(neighborhood_geometry):
    num_schools = schools[schools.geometry.intersects(neighborhood_geometry)].shape[0]
    num_subways = subways[subways.geometry.intersects(neighborhood_geometry)].shape[0]
    num_cultural_places = culutral_places[culutral_places.geometry.intersects(neighborhood_geometry)].shape[0]
    bike_path_length = bike_paths[bike_paths.geometry.intersects(neighborhood_geometry)].length.sum()
    park_area = parks[parks.geometry.intersects(neighborhood_geometry)].area.sum()
    sport_area = sport[sport.geometry.intersects(neighborhood_geometry)].area.sum()

    return num_schools, num_subways, num_cultural_places, bike_path_length, park_area, sport_area

neighborhoods[['num_schools', 'num_subways','num_cultural_places', 'bike_path_length', 'park_area', 'sport_area']] = neighborhoods.geometry.apply(
    lambda geom: pd.Series(analyze_neighborhood_postive_aspects(geom))
)

# region air
def calculate_weighted_pollution(neighborhood_geometry, air_emmisions, air_pollution_element):

    intersection = gpd.overlay(air_emmisions, gpd.GeoDataFrame(geometry=[neighborhood_geometry], crs=air_emmisions.crs), how='intersection'
                               , keep_geom_type=False)


    intersection['area'] = intersection.geometry.area

    total_area = intersection['area'].sum()
    if total_area == 0 or intersection.empty:
        return 0
    avg = (intersection[air_pollution_element] * intersection['area']).sum() / total_area

    return avg


pollution_columns = ["sum_ozone", "sum_nitrogen", "sum_nitric", "sum_black_carbon"]

for col in pollution_columns:
    neighborhoods[col] = neighborhoods.geometry.apply(lambda geom: calculate_weighted_pollution(geom, air_emmisions, col))

neighborhoods['chemicals_in_the_air'] = (
    neighborhoods['sum_ozone'] +
    neighborhoods['sum_nitrogen'] +
    neighborhoods['sum_nitric'] +
    neighborhoods['sum_black_carbon']
)
# endregion

def analyze_neighborhood_negative_aspects(neighborhood_geometry):
    num_traffic = traffic[traffic.geometry.intersects(neighborhood_geometry)].shape[0]
    num_arrests = arrests[arrests.geometry.intersects(neighborhood_geometry)].shape[0]
    num_noise_complain = noise_complain[noise_complain.geometry.intersects(neighborhood_geometry)].shape[0]

    return num_traffic, num_arrests, num_noise_complain

neighborhoods[['num_traffic', 'num_arrests', 'num_noise_complain']] = neighborhoods.geometry.apply(
    lambda geom: pd.Series(analyze_neighborhood_negative_aspects(geom))
)


# region Fill NaN using 5000m buffer and neighbors

from shapely.geometry import Polygon

columns_to_fill = ['chemicals_in_the_air', 'num_traffic', 'num_arrests', 'num_noise_complain']

for col in columns_to_fill:
    neighborhoods[col].replace(0, np.nan, inplace=True)

buffered_neighborhoods = neighborhoods.copy()
buffered_neighborhoods['geometry'] = buffered_neighborhoods.geometry.buffer(10000)


for col in columns_to_fill:
    updated_values = {}

    for idx, row in neighborhoods.iterrows():
        if np.isnan(row[col]):

            neighbors = neighborhoods[buffered_neighborhoods.geometry.iloc[idx].intersects(neighborhoods.geometry)]


            mean_value = neighbors[col].mean()

            if not np.isnan(mean_value):
                updated_values[idx] = mean_value

    for idx, value in updated_values.items():
        neighborhoods.at[idx, col] = value

print(neighborhoods['num_noise_complain'].isna().sum())

# endregion


#normalizacja wynikow
scaler = MinMaxScaler()

positive_cols = ['num_schools', 'num_subways', 'num_cultural_places', 'bike_path_length', 'park_area', 'sport_area']
negative_cols = ['num_traffic', 'num_arrests', 'num_noise_complain', 'chemicals_in_the_air']

neighborhoods[positive_cols] = scaler.fit_transform(neighborhoods[positive_cols])
neighborhoods[negative_cols] = scaler.fit_transform(neighborhoods[negative_cols])

#tworzenie wynikow
neighborhoods['positive_score'] = (neighborhoods['num_schools'] + neighborhoods['num_subways']
+ neighborhoods['num_cultural_places'] + neighborhoods['bike_path_length'] + neighborhoods['park_area'] + neighborhoods['sport_area'])


neighborhoods['negative_score'] = (neighborhoods['num_traffic'] + neighborhoods['num_arrests'] + neighborhoods['num_noise_complain']
                                   + neighborhoods['chemicals_in_the_air'])

neighborhoods['live_score'] = neighborhoods['positive_score'] - neighborhoods['negative_score']

neighborhoods['live_score'] = neighborhoods['live_score'].round(2)

neighborhoods = neighborhoods.to_crs(epsg=4326)
neighborhoods.to_file("data/neighborhoods_ready.geojson", driver="GeoJSON")