source /Users/vishakh/miniconda3/bin/activate;
git checkout github-action
git pull
python3 scraper.py > data.json;
now="$(TZ=America/Los_Angeles date -v -1d +'%m/%d/%Y')"
git add data.json
git commit -m "Updated data.json for ${now}"
git push
