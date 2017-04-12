# iTunes store review
## Access
Access to the reviews is publically available via RSS feeds. E.g.
```
https://itunes.apple.com/gb/rss/customerreviews/page=1/id=APPID/sortby=mostrecent/xml?urlDesc=/customerreviews/id=APPID/xml
```
where `APPID` is replaced with the store ID of your app.
## The .conf file
The itunes conf file contains the following parameters:
- path_log: Location where you want to store the log of the script
- path_rev: Location where you want to store the output JSON containing the reviews
- translate_key: Google developer API key for the translation
- doNotTranslate: A list of countries that shouldn't be translated
- countries: A list of countries whose store we want to look at
- app_ids: List of iTunes app IDs
- app_names: List of the corresponding app names (in the same order)

More about the Google Translate API is below. 

The countries need to be in the form of two letter country codes, e.g. 'US', 'GB', 'FR' etc.

The script expects the last four entries to be lists. If only one value is require, e.g. only one app, then still give it in list form, e.g.
```
app_ids: ['12345678']
app_names: ['MyApp']
```

An example itunes.conf file can be found in this project.
## Script
We perform two checks to decide if the review should be logged:
- Date check - is it within our date range
- Log check - have we already logged this review

The script by default looks into the last 6 days of reviews. There is a command line flag `-a` which accepts either `y` or `n` as a parameter, with `n` the default. If we want to backfill the data (i.e. enable logging for all reviews), `-a y` should be specified. 

If `-a n` then we proceed with checking the date of the review. If it's within our specified date range (the current day and the previous 6 days) we carry on, else we move on to the next review.

Next we check if we have already logged this review. This can be done via the unique review `id`. If a review with this ID already appears in the log file, the review is skipped.

Translation is by default enabled. If you want to disable it (e.g. if you have no access to the Google Translate API), simply use `-t n` when running the script from command line.
### Peculiarities in the code
As we're making repeated requests to the same place we need to be careful not to get blocked. Another problem is that we sometimes experience some server-side caching. In an attempt to circumvent these things we a) specify a browser and b) specify no caching.
```python
request.add_header('User-Agent', 'Mozilla/5.0') 
request.add_header('Cache-Control', 'no-cache')
```

The XML file has name spaces and attributes in it which makes querying it a little more difficult. Therefore we first strip the code of these namespaces to facilitate the reading in of data.
```python
it = ET.iterparse(StringIO(xml_data))
for _, el in it:
    if '}' in el.tag:
         el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
    for at in el.attrib.keys(): # strip namespaces of attributes too
        if '}' in at:
            newat               = at.split('}', 1)[1]
            el.attrib[newat]    = el.attrib[at]
            del el.attrib[at]
    xml_data2 = it.root # cleaned data
```
## Requirements
A `requirements_itunes.txt` file can be found in this project. To install the requirements, use
```
pip install -r requirements_itunes.txt
```

