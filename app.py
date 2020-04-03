from flask import Flask
from scraper import pipeline
app = Flask(__name__)

@app.route('/scrape')
def scrape():
    bay_area_counties = [
        'Solano County, California, United States',
        'Alameda County, California, United States',
        'Santa Clara County, California, United States',
        'San Francisco County, California, United States',
        'Contra Costa County, California, United States',
        'San Mateo County, California, United States',
        'Sonoma County, California, United States',
        'Napa County, California, United States',
        'Marin County, California, United States'
    ]
    return pipeline(bay_area_counties);

if __name__ == '__main__':
    app.run()
