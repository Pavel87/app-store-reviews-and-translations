'''Copyright 2017 Shazam Entertainment Limited

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.

You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

'''

from __future__ import division
import time
import argparse
import json
import sys
import collections
import ConfigParser
from httplib2 import Http
from apiclient.discovery import build

def GetArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--text', required=True, action='store',
                       help='Text to translate')
    parser.add_argument('-s', '--path', required=True, action='store',
                       help='Path to config file')
    args = parser.parse_args()
    return args


def translate(translate_text, key):

    lang_code = "en"

    service = build('translate', 'v2', developerKey=key)
    if translate_text!=None:
        try:
            result = service.translations().list(target=lang_code,q=translate_text).execute()
            translation = result['translations'][0]['translatedText']
        except:
            print "There was an error with the translation."
            translation = None
    else:
        translation = None

    return translation


#------------------------------------------------

def main():

    # Get credentials
    args            = GetArgs()
    confpath        = args.path
    text            = args.text


    # Parse values and assign to variables
    config          = ConfigParser.ConfigParser()
    config.read("%s/google.conf"% confpath)
    translate_key   = config.get("translate", "translate_key")

    translated_text = translate(text, translate_key)
    print translated_text

    return

# Start program
if __name__ == "__main__":
    main()


