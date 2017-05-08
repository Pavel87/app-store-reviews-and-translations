'''Copyright 2017 Shazam Entertainment Limited

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.

You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

'''

from __future__ import division
import xml.etree.cElementTree as ET
import time
import datetime
import argparse
import json
import socket
import ast
import sys
import collections
import ConfigParser
import urllib2
from StringIO import StringIO
import requests
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


def translate(translate_text, key, log_f, hn):

    lang_code = "en"

    service = build('translate', 'v2', developerKey=key)
    if translate_text!=None:
        try:
            result      = service.translations().list(target=lang_code,q=translate_text).execute()
            translation = result['translations'][0]['translatedText']
        except:
            print "There was an error with the translation."
            log_f.write("%s %s itunes-rating: There was an error with the translation.\n" % (log_date(), hn))
            translation = None
    else:
        translation = None

    return translation

# create class
class reviews:

    def __init__(self, rev):
        self.rev = rev

    def time(self):  # time has to be in a certain format for Splunk use

        # Some definitions
        Months = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '04':'Apr', '05': 'May',\
                '06': 'Jun', '07': 'Jul', '08': 'Aug', '09': 'Sep', \
                '10': 'Oct', '11': 'Nov', '12': 'Dec'}
        time_itunes = self.rev.find('updated').text
        date, time_tz = time_itunes.split('T')
        Year, Month, Day = date.split('-')

        # separate time from timezone
        time_split = time_tz.split(':')
        time = time_split[0]+':'+time_split[1]+':'+time_split[2][:2]
        tz = time_split[2][2:]+':'+time_split[3]
        Month_lit = Months[Month]

        new_time = "%s/%s/%s:%s %s" %(Day, Month_lit, Year, time, tz)
        return new_time

    def id(self):
        return self.rev.find('id').text

    def title(self):
        return self.rev.find('title').text

    def content(self):
        c_return = None
        con = self.rev.findall('content')
        for c in con:
            ctype = c.get('type')
            if ctype == 'text':
                c_return = c.text
        return c_return

    def voteSum(self):
        return self.rev.find('voteSum').text

    def voteCount(self):
        return self.rev.find('voteCount').text

    def rating(self):
        return self.rev.find('rating').text

    def version(self):
        return self.rev.find('version').text

    def author(self):
        return self.rev.find('author').find('name').text

    def app_name(self):
        return self.rev.find('name').text


def log_date():
	return time.strftime("%b %d %H:%M:%S")

def file_date(t):
    # Date to use in review log file
    d           = datetime.datetime.strptime(t.split(':')[0], '%d/%b/%Y')
    date_new    = d.strftime("%Y%m%d")
    return date_new

def check_date(t):
    # Check whether the review was done in the last 6 days
    today   = datetime.date.today()
    margin  = datetime.timedelta(days = 6)
    t_new   = datetime.datetime.strptime('%s'%t.split(':')[0],'%d/%b/%Y').date()
    if (today-margin) <= t_new:
        print "This date can be logged"
        return_code = 0
    else:
        return_code = 1
    return return_code

def check_entry(id_entry, fp_rev, entry_time):
    # Only log the entry if it's not already present
    return_code = 0
    data_list =[]
    try:
        check_file = open("%s/reviews-%s.log"%(fp_rev, file_date(entry_time)), 'r')
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

def data_collection(page, url_path, cntry, notrans, log_f, fp_rev, hn, app_name, transkey, action, transflag):

    entry_count = 0

    # Query API
    print "Reading in XML file from %s..." % (cntry)
    try:
        request = urllib2.Request(url_path)
        request.add_header('User-Agent', 'Mozilla/5.0') # There are at times issues with caching
        request.add_header('Cache-Control', 'no-cache')
        file = urllib2.build_opener().open(request)
        xml_data = file.read()
        file.close()

        try:
            it = ET.iterparse(StringIO(xml_data))
            for _, el in it:
                if '}' in el.tag:
                    el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
            for at in el.attrib.keys(): # strip namespaces of attributes too
                if '}' in at:
                    newat               = at.split('}', 1)[1]
                    el.attrib[newat]    = el.attrib[at]
                    del el.attrib[at]
            xml_data2 = it.root
        except:
            print 'Error parsing this page'
            log_f.write("%s %s itunes-rating: Error parsing a page from %s.\n" % (log_date(), hn, cntry))


        if 'xml_data2' in locals():
            print "Successfully read in XML data from %s" % (cntry)
            log_f.write("%s %s itunes-rating: Succesfully read in XML data from %s.\n" % (log_date(), hn, cntry))

            count = 0
            max_count = len(xml_data2.findall('entry'))
            if max_count == 0 and page == 1:
                   print "No results found - there may be a problem with the link."
                   log_f.write("%s %s itunes-rating: ERROR - No results for %s. There may be a problem with the link.\n" % (log_date(), hn, cntry))
            for e in xml_data2.findall('entry'):
                r = reviews(e)
                if 0 < count < max_count:
                    # check if we want to look at this file
                    if action == 'y':
                        read_in = 0
                    else:
                        read_in = check_date(r.time())

                    if read_in == 0:
                        # check if entry already present in file
                        dupl_check = check_entry(r.id(), fp_rev, r.time())
                        if dupl_check == 0:
                            entry_count +=1
                            # Create ordered JSON dictionary to store the data
                            rev_dict                = collections.OrderedDict()
                            rev_dict["t"]           = r.time()
                            rev_dict["title"]       = r.title()
                            rev_dict["content"]     = r.content()
                            if cntry in notrans:
                                rev_dict["title_en"]   = rev_dict["title"]
                                rev_dict["content_en"] = rev_dict["content"]
                            elif transflag == 'n':
                                rev_dict["title_en"]    = None
                                rev_dict["content_en"]  = None
                            else:
                                rev_dict["title_en"]    = translate(r.title(), transkey, log_f, hn)
                                rev_dict["content_en"]  = translate(r.content(), transkey, log_f, hn)
                            rev_dict["id"]          = r.id()
                            rev_dict["voteSum"]     = r.voteSum()
                            rev_dict["voteCount"]   = r.voteCount()
                            rev_dict["rating"]      = r.rating()
                            rev_dict["version"]     = r.version()
                            rev_dict["author"]      = r.author()
                            rev_dict["country"]     = cntry
                            rev_dict["store"]       = "iTunes"
                            rev_dict["app_name"]    = app_name

                            # Stores Dictionary in a JSON file by review date
                            rev_file = open("%s/reviews-%s.log"%(fp_rev, file_date(r.time())),'a+')
                            rev_file.write(json.dumps(rev_dict)+"\n")
                            rev_file.close()
                        else:
                            pass
                count +=1
    except:
        print "Could not open URL"
        log_f.write("%s %s itunes-rating: ERROR - Could not open URL.\n" % (log_date(), hn))

    return entry_count


#------------------------------------------------

def main():

    # Get credentials
    args        = GetArgs()
    confpath    = args.path
    doAll       = args.all
    translate_flag  = args.translate

    # We can either only examine the previous day's data or backfill 
    if doAll != 'y' and doAll !='n':
        print 'Value for -a/-all flag %s not valid. Choose y or n'%doAll
        sys.exit(1)

    # Get credentials from .conf file
    config          = ConfigParser.ConfigParser()
    config.read("%s/itunes.conf"% confpath)
    filepath_log    = config.get("itunes_reviews", "path_log")
    filepath_rev    = config.get("itunes_reviews", "path_rev")
    translate_key   = config.get("itunes_reviews", "translate_key")
    noTransList     = ast.literal_eval(config.get("itunes_reviews", "doNotTranslate"))
    url_countries   = ast.literal_eval(config.get("itunes_reviews", "countries"))
    app_ids         = ast.literal_eval(config.get("itunes_reviews", "app_ids"))
    app_names       = ast.literal_eval(config.get("itunes_reviews", "app_names"))

    hostname        = socket.gethostname()

    log_file = open("%s/script-itunesrating.log"%(filepath_log),'a+')
    log_file.write("%s %s itunes-rating: script started\n"%(log_date(),hostname))
    if doAll == 'y':
        print "All entries will be logged."
        log_file.write("%s %s itunes-rating: All entries will be logged.\n"%(log_date(),hostname))

    
    app_dict = dict(zip(app_ids, app_names))

    for url_country in url_countries:
        country         = url_country
        country_entries = 0 # Count the number of new entries per country

        for url_id in app_ids:
            entries     = 0
            app_name    = app_dict[url_id]
            print 'Querying data for %s from %s' % (app_name, country)
            log_file.write("%s %s itunes-rating: Querying data for %s from %s \n"%(log_date(),hostname, app_name, country))
            for i in range(1,11):
                print "Collecting data from page %i" % (i)
                log_file.write("%s %s itunes-rating: Collecting data from page %i for %s \n"%(log_date(),hostname, i, country))
                url_add         = 'https://itunes.apple.com/%s/rss/customerreviews/page=%i/id=%s/sortby=mostrecent/xml?urlDesc=/customerreviews/id=%s/xml' % (country, i, url_id, url_id)
                entries         = data_collection(i, url_add,country, noTransList, log_file, filepath_rev, hostname, app_name, translate_key, doAll, translate_flag)
                country_entries += entries
            print "%s entries logged for %s in %s" %(country_entries, app_name, country)
            log_file.write("%s %s itunes-rating: %s entries logged for %s in %s \n"%(log_date(),hostname, country_entries, app_name, country))
    log_file.close()
    return


# Start program
if __name__ == "__main__":
    main()


