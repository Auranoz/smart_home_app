import requests
import json
from django.conf import settings
from django.http import HttpResponse

headers = {'Authorization': 'Bearer {}'.format(settings.SMART_HOME_ACCESS_TOKEN)}
url = settings.SMART_HOME_API_URL


def get_request():
    r = requests.get(url, headers=headers)
    data = {}
    try:
        if r.json()['status'] != 'ok':
            HttpResponse(status=502)

        for element in r.json()['data']:
            data[element['name']] = element['value']
    except json.decoder.JSONDecodeError:
        HttpResponse(status=502)

    return data


def post_request(data_list):
    # data_list must be format like: [{'name': 'some_name', 'value': 'some_value'}, {...}]
    data = {'controllers': data_list}
    return requests.post(url, headers=headers, data=json.dumps(data))


get_api_data = get_request()
