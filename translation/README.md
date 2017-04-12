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

