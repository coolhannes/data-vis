import civis
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
from urllib.request import urlopen

### Get a Civis API Key: https://platform.civisanalytics.com/spa/users/profile
CIVIS_API_KEY=open('civis_key.txt').readline().rstrip()

### Get zip code level data into a pandas dataframe
# Read zip code tallies from Civis (Redshift)
sql = """
select 
	z.county_fips,
    left(z.county_fips,2) as state_fips,
    count(*) as responses
from dfp_analytics.dfp_surveys_wide w
join dfp_analytics_staging.dfp_zip_to_county z
	on z.zip_code = lpad(w.rider_zip,5,'0')
    and w.rider_zip is not null
group by 1
"""

df = civis.io.read_civis_sql(
    sql, 
    database = "TMC", 
    use_pandas = True,
    api_key=CIVIS_API_KEY
)

# Log scale since the vast majority of counties have very few respondents
# Making sure we don't lose leading zeros
df['responses'] = np.log10(df['responses'])

df['county_fips'] = df['county_fips'].astype(str)
df['county_fips'] = df.county_fips.str.pad(5,side = 'left', fillchar = '0')

# Pull values for the color range / scale
min_val = df.responses.min()
max_val = df.responses.max()    

# Steal the geojson county file from the plotly dataset
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

# The Albers USA projection is the classic map of the US, with AK and HI to the south west
fig = px.choropleth(df, geojson=counties, locations='county_fips', color='responses',
                           color_continuous_scale="Plasma",
                           range_color=(min_val, max_val),
                           projection="albers usa",
                           basemap_visible = True,
                           labels={'responses':'Survey Responses (Log Scale)'}
                          )

# If the map is not national, use the fitbounds feature to focus on a map area
if len(pd.unique(df['state_fips'])) == 1:
    fig.update_geos(fitbounds = "locations")

# Add some padding
fig.update_layout(margin={"r":10,"t":10,"l":10,"b":10})

# PNG Render
pio.write_image(fig,"responses.png", width=1000, height=500, scale=1)

#fig.show()
