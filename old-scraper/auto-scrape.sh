now=`date`;
# replaces all spaces and colons in date with dashes
# to make valid git branch name
branch_now=`echo "$now" | sed 's/[ :]/-/g'`;
git checkout -b "data-$branch_now";
source env/bin/activate;
python3 scraper.py;
git add data/covid_19_sf.csv;
git commit -m "Add SF data -- $now";
git push --set-upstream origin "data-$branch_now";
