from flask import Flask
from scraper import pipeline
app = Flask(__name__)

@app.route('/scrape')
def scrape():
    bay_area_counties = [
        'Solano County, CA, USA',
        'Alameda County, CA, USA',
        'Santa Clara County, CA, USA',
        'San Francisco County, CA, USA',
        'Contra Costa County, CA, USA',
        'San Mateo County, CA, USA',
        'Sonoma County, CA, USA',
        'Napa County, CA, USA',
        'Marin County, CA, USA'
    ]
    return pipeline(bay_area_counties);

if __name__ == '__main__':
    app.run()
