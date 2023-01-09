COPIED FROM RECOGNITION SERVICE; URL IS ONLY EXAMPLE

## Rasa Server
The rasa server can be addressed directly by sending POST requests to [http://20.79.206.115:5005/webhooks/rest/webhook](http://20.79.206.115:5005/webhooks/rest/webhook).
A Json body is expected. It follows the struture:
```JSON
{
    "sender" : "{SENDER}", 
    "message": "{MESSAGE TEXT}"
}
```
It returns a JSON of the structure 
```JSON
{
  "recipient_id" : "{SENDER}", 
  "text": {
    "Street": "{STREET or null}", 
    "House Number": "{HOUSE NUMBER or null}",
    "Postal Code": "{POSTAL CODE or null}",
    "City": "{CITY or null}"
  }
}
```
  
An example for a request using curl would be
```shell
curl -X POST -H "Content-Type: application/json" -d '{"sender" : "sender", "message": "I live in Leipzig"}' http://20.79.206.115:5005/webhooks/rest/webhook
```
The returned answer looks like
```shell
[{"recipient_id":"sender","text":"{\"Street\": \"Leipzig\", \"House Number\": null, \"Postal Code\": null, \"City\": null}"}]
```
Other working text-examples can be found in the section [Frontend](#frontend).

