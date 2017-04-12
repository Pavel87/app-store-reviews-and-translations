# Google Play store review
## Access
Access to the Google Play reviews is through the Google Play Developer API. This means you must have access to a developer account for the app. In our case we use a service account so we will need OAuth 2.0 level authentication. For more information on how to set this up, see [here](https://developers.google.com/android-publisher/getting_started#setting_up_api_access_clients). There are different methods of then authenticating (see [here](https://developers.google.com/identity/protocols/OAuth2ServiceAccount)) but we're using the method involving a JSON file.
```python
# Validate google developer credentials
scopes          = ['https://www.googleapis.com/auth/androidpublisher']
credentials     = ServiceAccountCredentials.from_json_keyfile_name('%s/%s'%(filepath_conf,review_key_file), scopes=scopes)
try:
    service = build('androidpublisher', 'v2', http=credentials.authorize(Http()))
except:
    print "There was an error connecting."
    sys.exit(1)
```
## The .conf file
The Google Play store conf file contains the following parameters:
- path_log: Location where you want to store the log of the script
- path_rev: Location where you want to store the output JSON containing the reviews
- path_conf: Location of the Google Play store credential file
- review_key_file: Name of the Google Play store credential file (JSON)
- translate_key: Google developer API key for the translation
- app_name: Name of the app
- package_name: Name of the package as needed for review collection

More about the Google Translate API is below. 

The credential file needs to be generated as explained above. The package name is of the form 'com.package.android' and tells the API which app to gather the data for.

An example android.conf file can be found in this project.
## Script
We perform two checks to decide if the review should be logged:
- Date check - is it within our date range
- Log check - have we already logged this review

The script by default looks into the last 1 day of reviews. There is a command line flag `-a` which accepts either `y` or `n` as a parameter, with `n` the default. If we want to backfill the data (i.e. enable logging for all reviews), `-a y` should be specified. 

If `-a n` then we proceed with checking the date of the review. If it's within our specified date range (the current day and the previous day) we carry on, else we move on to the next review.

Next we check if we have already logged this review. This can be done via the unique review `id`. If a review with this ID already appears in the log file, the review is skipped.

Unlike the iTunes script we cannot query by country. We can, however, decide how many pages of reviews to look at. By default, we look at 5 pages and 12 when we backfill, though this can be amended.
```python
if doAll == 'y':
    page_limit  = 12
    print "All entries will be logged."
else:
    page_limit  = 5
    print 'Logging dates between', today, 'and', (today-margin)

...

# Fetch all reviews
page_count          = 0 # This determines how far back we go
while "tokenPagination" in reviews_page:
    time.sleep(5)
    page_count += 1
    print "Reading in page", page_count
    reviews_page = reviews_resource.list(packageName=package_name,
                                   token=reviews_page["tokenPagination"]["nextPageToken"],
                                   maxResults=1000).execute()
    reviews_list.extend(reviews_page["reviews"])

    if page_count > page_limit:
        break
```
These numbers depend on how many reviews you get or how far back you want to go.

Translation is by default enabled. If you want to disable it (e.g. if you have no access to the Google Translate API), simply use `-t n` when running the script from command line.
## Requirements
A `requirements_android.txt` file can be found in this project. To install the requirements, use
```
pip install -r requirements_android.txt
```
Most importantly the `oauth2client` module is required to authenticate to the store.
