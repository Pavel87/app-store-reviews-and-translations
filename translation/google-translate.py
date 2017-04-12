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


def translate(textToTranslate, key):

    toLangCode = "en"

    service = build('translate', 'v2', developerKey=key)
    if textToTranslate!=None:
        try:
            result = service.translations().list(target=toLangCode,q=textToTranslate).execute()
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


