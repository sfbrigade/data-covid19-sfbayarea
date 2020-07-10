source_url = 'https://dashboard.cchealth.org/sense/app/93b7808b-5a6d-4e9a-9161-ed2eafeb4afc/sheet/7878ea82-880a-4644-bbd6-97f2719e3756/state/analysis'

# Find Total Cases Reported by Day
# Right click, select "View data"
#   find <div> with attr tid= 'context-menu'
            # find li with index 2, and/or li with <span> with attr title = "View data"
# find h1 that says 'Total Cases Reported by Day"
# find table after the h1
# find <body>
# grab first two <td> cells of each <tr> in the body (first is date, second is total # of positive cases)
# scroll down one click, get last row with each click
# when to stop? check when have scrolled to the bottom?
