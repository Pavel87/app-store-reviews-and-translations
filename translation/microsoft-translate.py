'''Copyright 2017 Shazam Entertainment Limited

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.

You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

'''

from __future__ import division
import xml.etree.cElementTree as ET
import time
import argparse
import ConfigParser
import urllib2
import codecs
import json
import requests
import urllib
from xml.etree import ElementTree



def GetArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--text', required=True, action='store',
                       help='Text to translate')
    parser.add_argument('-s', '--path', required=True, action='store',
                       help='Path to config file')
    args = parser.parse_args()
    return args
    

def get_token(client, client_token): 
    urlArgs = {
        'client_id': '%s' % client,
        'client_secret': '%s' % client_token,
        'scope': 'http://api.microsofttranslator.com',
        'grant_type': 'client_credentials'
    }

    oauthUrl = 'https://datamarket.accesscontrol.windows.net/v2/OAuth2-13'

    try:
        # get token
        oauth_token = json.loads(requests.post(oauthUrl, data = urllib.urlencode(urlArgs)).content) 
        final_token = "Bearer " + oauth_token['access_token'] 
    except OSError:
        pass

    return final_token

def translate(final_token,translate_text):

    lang_code = "en"

    translate_text = codecs.encode(translate_text,'utf-8')   
    url_text = urllib2.quote(translate_text)

    # Call to Microsoft Translator Service
    headers = {"Authorization ": finalToken}
    translate_url = "http://api.microsofttranslator.com/v2/Http.svc/Translate?text={}&to={}".format(url_text, lang_code)

    try:
        translation_data = requests.get(translate_url, headers = headers) #make request
        translation = ElementTree.fromstring(translation_data.text.encode('utf-8')).text # parse xml return values  
        if translation == None:
            print "ERROR: Translation didn't work. Check token."
            print translation_data.text.encode('utf-8')

    except:
        translation = None
        print "Translation unsuccessful."

    return translation


#------------------------------------------------

def main():
    
    # Get credentials
    args            = GetArgs()
    confpath        = args.path
    text            = args.text

    # Parse values and assign to variables
    config          = ConfigParser.ConfigParser()
    config.read("%s/microsoft.conf"% confpath)
    client_id       = config.get("translate", "client_id")
    client_token    = config.get("translate", "client_token")

    # Generate token
    finalToken      = GetToken(client_id, client_token)
    token_time      = time.time()

    # Check if toke still valid
    # Only necessary for more complex scripts
    current_time = time.time()
    if current_time > (token_time + (5*60)):
        token_time = current_time
        final_token = get_token(client_id, client_token)
        print "Token renewed" 

    translated_text    = translate(final_token,text)
    print translated_text

    return


# Start program
if __name__ == "__main__":
    main()


