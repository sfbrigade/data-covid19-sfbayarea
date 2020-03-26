git checkout master;
source env/bin/activate;
python3 scraper.py;
git add data/covid_19_sf.csv;
now=`date`;
git commit -m "Add SF data -- $now";
git push;
