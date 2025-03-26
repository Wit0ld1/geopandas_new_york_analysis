import folium
import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium

gdf = gpd.read_file("data/neighborhoods_ready.geojson")

st.title("New York City Quality of Life Analysis")

st.sidebar.header("Set wage of positive aspect")
w_schools = st.sidebar.slider("Schools", 0.0, 1.0, 0.1)
w_subways = st.sidebar.slider("Metro", 0.0, 1.0, 0.1)
w_cultural = st.sidebar.slider("Cultural places", 0.0, 1.0, 0.1)
w_bike = st.sidebar.slider("Bike paths", 0.0, 1.0, 0.1)
w_parks = st.sidebar.slider("Parks", 0.0, 1.0, 0.1)
w_sport = st.sidebar.slider("Sport objects", 0.0, 1.0, 0.1)

st.sidebar.header("Set wage of negative aspect")
w_traffic = st.sidebar.slider("Traffic", 0.0, 1.0, 0.1)
w_arrests = st.sidebar.slider("Arrests", 0.0, 1.0, 0.1)
w_noise = st.sidebar.slider("Noise", 0.0, 1.0, 0.1)
w_pollution = st.sidebar.slider("Chemicals in the air", 0.0, 1.0, 0.1)


gdf['positive_score'] = (
    gdf['num_schools'] * w_schools +
    gdf['num_subways'] * w_subways +
    gdf['num_cultural_places'] * w_cultural +
    gdf['bike_path_length'] * w_bike +
    gdf['park_area'] * w_parks +
    gdf['sport_area'] * w_sport
)

gdf['negative_score'] = (
    gdf['num_traffic'] * w_traffic +
    gdf['num_arrests'] * w_arrests +
    gdf['num_noise_complain'] * w_noise +
    gdf['chemicals_in_the_air'] * w_pollution
)

gdf['live_score'] = (gdf['positive_score'] - gdf['negative_score']).round(2)


m = folium.Map(location=[40.730610, -73.935242], zoom_start=9)



data = gdf[['neighborhood', 'live_score']]



folium.Choropleth(
    geo_data=gdf,
    name='live_score',
    data=gdf,
    columns=['neighborhood', 'live_score'],
    key_on='feature.properties.neighborhood',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name='Live Score dla dzielnic'
).add_to(m)

for _, row in gdf.iterrows():
    folium.GeoJson(
        row['geometry'],
        tooltip=folium.Tooltip(
            f"{row['neighborhood']}<br>Live Score: {row['live_score']:.2f}"
        ),
        style_function=lambda x: {
            'fillOpacity': 0,
            'color': 'transparent'
        }
    ).add_to(m)



st_data = st_folium(m, height=700, use_container_width=True)
