# App Store reviews
As you can imagine we at Shazam need to keep an eye on how well our app is doing and listen to the feedback of our users. There are tools online that you can pay for to do that job for you - but why do that when you can do it yourself?! Different stores, e.g. iOS/iTunes and Android/Google Play are accessed in different ways and require different access level. The following will explain some of the prerequisites for the Python scripts we use to analyse our app's data. 

As we want to know what people all over the world are saying, not just in English speaking countries, we translate the reviews. In the two scripts presented here you will see two different APIs you could use (more about that below). 

# Code covered in these scripts
All the scripts are in Python and output JSON files in a format that is friendly with [Splunk](www.splunk.com). The following methods are covered in the script:

- Microsoft Translate API (microsoft-translate.py)
- Google Translate API (google-translate.py, google-play-rathing.py, itunes-rating.py)
- Scraping iTunes review data from XML (itunes-rating.py)
- Retrieving Google Play review data using the android publisher API (google-play-rating.py)

I like working with config files that contain usernames, passwords, secret keys and storage information to keep the scripts as general and transferable as possible. Examples of these are included in this project and the parameters are explained briefly.
# iTunes store review
## Access
Access to the reviews is publically available via RSS feeds.
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
As we're making repeated requests to the same place we need to be careful not to get blocked. Another problem is that we sometimes experience some server side caching. In an attempt to circumvent these things we a) specify a browser and b) specify no caching.
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
# Output format
The scripts above print individual JSON objects to the designated file. They are not a comma separated list but instead objects on separate lines. The outputs differ slightly between iTunes and Google Play but are very similar. The format is as follows:
```JSON
{
  "t": "06/Apr/2017:12:11:10",
  "title": "This is a title in the original language",
  "content": "This is the review in the orginal language! ",
  "title_en": "This is the title in English",
  "content_en": "This is the review in English",
  "id": "1234abcd5678efgh",
  "rating": 5,
  "version": "1.1.1",
  "device": "MyDevice",
  "os_version": 1.1,
  "author": "John Smith",
  "country": "GB",
  "store": "Android",
  "app_name": "MyApp"
}
```
The `id` is a unique identifier in the app and is used in the script to avoid replication. If no title is specified in the review (as is often the case for the Play store) the value will be `null`. Note that the time format was chosen to be recognised by the app Splunk.
# Translation APIs
## Google Translate
### Access
Access to the API can be gained through the Google Cloud console. In the API Manager, click 'Enable API' and search for the Google Cloud Translation API. A key can then be generated and stored.
##### .conf file
The config file only has one parameter:
- translate_key: The developer access key for the API

An example of the structure can be found in google.conf

### Script
 The text to be translated is passed as a command line argument like `-t "Text to translate"`.
 The key and the text to be translated are passed to the `translate` function. The language to be translated to is specified in the `toLangCode` variable. There is no need to define the *from* language as it is detected automatically.
The `result` variable will return a dictionary (i.e. JSON format). If the token is invalid the script will return an error.

### Requirements
To run this script [google-api-python-client](https://pypi.python.org/pypi/google-api-python-client/) needs to be installed. This can be done using pip or other methods of your choice:
```
pip install google-api-python-client
```
## Microsoft Translate

**Note: This is deprecated. You now have to access through Cognitive Services in the Azure Portal rather than through Datamarket.**
##### Access
Previously you had to have an account in Microsoft Datamarket and create a project there. Now you need to have an Azure account/subscription. In the portal you will find the Cognitive Services under Intelligence + Analytics. As we've only used the Datamarket version I am not sure how to proceed from that.

### .conf file
The config file has the following parameters:
- client_id: This is the Microsoft project ID for the translation
- client_token: This is the Microsoft project token for the translation

An example of the structure can be found in microsoft.conf

### Script
The script is overall pretty self-explanatory. The text to be translated is passed as a command line argument like `-t "Text to translate"`. 
It first performs a check on the current token generated using the access credentials (see the `if` statement). For a one-off script like this where only one single input is translated this is not necessary as the token generated should be valid for 10 minutes. However if multiple translations are performed in a script running for a long time (as may be the case for retrieving reviews) the token has to be renewed regularly. To see how the token is generated, look at the `GetToken` function.
The `translate` function performs the translation itself and requires the token and the text to be translated. The language to be translated to should be specified using the `toLangCode` variable. You do not, however, need to pass the language that you want to translate *from* as this can be detected automatically.

Note: As we are using the *requests* package we are passing a URL to query the API. Therefore the text that is to be translated needs to have the correct format. This is achieved in these lines:
```python
    textToTranslate = codecs.encode(textToTranslate,'utf-8')   
    url_text        = urllib2.quote(textToTranslate)
```
The request returns an XML string. If the translation fails the result returned will be `None`. To troubleshoot print out the XML output though the token is likely invalid causing the translation to fail.
