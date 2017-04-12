from __future__ import division
import time
import datetime
import argparse
import json
import socket
import sys
import collections
import ConfigParser
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build

def GetArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--path', required=True, action='store',
                       help='Path to config file')
    parser.add_argument('-a', '--all', required=False, action='store', default='n',
                       help='Do all entries')
    parser.add_argument('-t', '--translate', required=False, action='store', default='y',
                       help='Translate the reviews')
    args = parser.parse_args()
    return args


def translate(textToTranslate, key, log_f, hn):

    toLangCode = "en"

    service = build('translate', 'v2', developerKey=key)
    if textToTranslate!=None:
        try:
            result = service.translations().list(target=toLangCode,q=textToTranslate).execute()
            translation = result['translations'][0]['translatedText']
        except:
            print "There was an error with the translation."
            log_f.write("%s %s android-rating: There was an error with the translation.\n" % (log_date(), hn))
            translation = None
    else:
        translation = None

    return translation

# create class
class reviews:

    def __init__(self, rev):
        self.rev = rev

    def time(self):
        ts = self.rev["comments"][0]["userComment"]["lastModified"]["seconds"]
        # Time given in unix timestamp format
        ts_dt = datetime.datetime.fromtimestamp(float(ts))
        new_time = ts_dt.strftime("%d/%b/%Y:%H:%M:%S")     
        return new_time

    def id(self):
        return self.rev["reviewId"]

    def content(self):
        comments = self.rev["comments"][0]["userComment"]["text"]
        t_return, c_return = comments.split('\t')[0], comments.split('\t')[1]
        if t_return == '':
            t_return = None
        return t_return, c_return

    def rating(self):
        return self.rev["comments"][0]["userComment"]["starRating"]

    def version(self):
        try:
            version = self.rev["comments"][0]["userComment"]["appVersionName"]
        except:
            version = None
        return version

    def author(self):
        try:
            auth = self.rev["authorName"]
            if auth == '':
                auth = None
        except:
            auth=None
        return auth

    def lang(self):
        return self.rev["comments"][0]["userComment"]["reviewerLanguage"]


    def country(self):
        lng = self.lang()
        country = lng.split('_')[1]
        return country

    def device(self):
        try:
            device = self.rev["comments"][0]["userComment"]["device"]
        except:
            device = None
        return device

    def os_version(self):
        try:
            os_version = self.rev["comments"][0]["userComment"]["androidOsVersion"]
        except:
            os_version = None
        return os_version


def log_date():
	return time.strftime("%b %d %H:%M:%S")

def file_date(t):
    # Date to use in review log file
    d           = datetime.datetime.strptime(t.split(':')[0], '%d/%b/%Y')
    date_new    = d.strftime("%Y%m%d")
    return date_new

def check_date(t):
    # Check whether the review was done in the last day
    today       = datetime.date.today()
    margin      = datetime.timedelta(days = 1)
    t_new       = datetime.datetime.strptime('%s'%t.split(':')[0],'%d/%b/%Y').date()
    if (today-margin) <= t_new:
        return_code = 0
    else:
        return_code = 1
    return return_code

def check_entry(id_entry, fp_rev, entry_time):
    # Only log the entry if it's not already present
    return_code = 0
    data_list   = []
    try:
        check_file = open("%s/reviews-android-%s.log"%(fp_rev, file_date(entry_time)), 'r')
        for line in check_file:
            data_list.append(json.loads(line))
        for obj in data_list:
            for key, value in obj.iteritems():
                    if key == 'id':
                        if value == id_entry:
                            return_code = 1
                            break
        check_file.close()
    except:
        return_code = 0
    
    return return_code


#------------------------------------------------

def main():

    # Get credentials
    args            = GetArgs()
    confpath        = args.path
    doAll           = args.all
    translate_flag  = args.translate

    # We can either only examine the previous day's data or backfill 
    if doAll != 'y' and doAll !='n':
        print 'Value for -a/-all flag %s not valid. Choose y or n'%doAll
        sys.exit(1)

    # Get credentials from .conf file
    config          = ConfigParser.ConfigParser()
    config.read("%s/android.conf"% confpath)
    filepath_log    = config.get("android_reviews", "path_log")
    filepath_rev    = config.get("android_reviews", "path_rev")
    filepath_conf   = config.get("android_reviews", "path_conf")
    review_key_file = config.get("android_reviews", "review_key_file")
    translate_key   = config.get("android_reviews", "translate_key")
    app_name        = config.get("android_reviews", "app_name")
    package_name    = config.get("android_reviews", "package_name")

    hostname        = socket.gethostname()

    log_file        = open("%s/script-androidrating.log"%(filepath_log),'a+')
    log_file.write("%s %s android-rating: script started.\n"%(log_date(),hostname))

    # Google Play store gets a lot of reviews so no need to go back
    today           = datetime.date.today()
    margin          = datetime.timedelta(days = 1)

    if doAll == 'y':
        page_limit  = 12
        print "All entries will be logged."
        log_file.write("%s %s android-rating: All entries will be logged.\n"%(log_date(),hostname))
    else:
        page_limit  = 5
        print 'Logging dates between', today, 'and', (today-margin)
        log_file.write("{} {} android-rating: Logging dates between {} and {}.\n".format(log_date(),hostname, today, (today-margin)))

    # Validate google developer credentials
    scopes          = ['https://www.googleapis.com/auth/androidpublisher']
    credentials     = ServiceAccountCredentials.from_json_keyfile_name(
    '%s/%s'%(filepath_conf,review_key_file), scopes=scopes)
    try:
        service = build('androidpublisher', 'v2', http=credentials.authorize(Http()))
    except:
        print "There was an error connecting."
        sys.exit(1)


    reviews_resource    = service.reviews()
    reviews_page        = reviews_resource.list(packageName=package_name, maxResults=1000).execute()
    reviews_list        = reviews_page["reviews"]

    log_file.write("%s %s android-rating: Connected to Google. Fetching reviews..\n"%(log_date(),hostname))

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

    print len(reviews_list), 'reviews found.'
    log_file.write("%s %s android-rating: %i reviews found.\n"%(log_date(),hostname, len(reviews_list)))


    rev_count = 0
    for rev in reviews_list:
        r = reviews(rev)
        if doAll == 'y':
            read_in = 0
        else:
            read_in = check_date(r.time())

        if read_in == 0:
            # check if entry already present in file
            dupl_check = check_entry(r.id(), filepath_rev, r.time())
            if dupl_check == 0:
                rev_count               += 1
                rev_dict                = collections.OrderedDict()
                rev_dict["t"]           = r.time()
                rev_dict["title"], rev_dict["content"]     = r.content()
                if 'en' in r.lang():
                    rev_dict["title_en"]    = rev_dict["title"]
                    rev_dict["content_en"]  = rev_dict["content"]
                elif 'en' not in r.lang() and translate_flag == 'y':
                    rev_dict["title_en"]    = translate(rev_dict["title"], translate_key, log_file, hostname)
                    rev_dict["content_en"]  = translate(rev_dict["content"], translate_key, log_file, hostname)
                else:
                    rev_dict["title_en"]    = None
                    rev_dict["content_en"]  = None
                rev_dict["id"]          = r.id()
                rev_dict["rating"]      = r.rating()
                rev_dict["version"]     = r.version()
                rev_dict["device"]      = r.device()
                rev_dict["os_version"]  = r.os_version()
                rev_dict["author"]      = r.author()
                rev_dict["country"]     = r.country()
                rev_dict["store"]       = "Android"
                rev_dict["app_name"]    = app_name

                rev_file                = open("%s/reviews-android-%s.log"%(filepath_rev, file_date(r.time())),'a+')
                rev_file.write(json.dumps(rev_dict)+"\n")
                rev_file.close()
    print rev_count, 'reviews logged.'
    log_file.write("%s %s android-rating: %i reviews logged.\n"%(log_date(),hostname, rev_count))
    log_file.write("%s %s android-rating: script finished.\n"%(log_date(),hostname))
    log_file.close()
    return

# Start program
if __name__ == "__main__":
    main()


