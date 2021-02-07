from __future__ import absolute_import, unicode_literals
from celery import task

from .models import Setting

from .request_mixin import get_request, post_request
from django.core.mail import send_mail
from django.conf import settings


@task()
def smart_home_manager():
    post_data = []
    cur_conditions = get_request()

    # 1 условие
    if cur_conditions['leak_detector'] and (cur_conditions['cold_water'] or cur_conditions['hot_water']):
        data = [
            {'name': 'cold_water', 'value': False},
            {'name': 'hot_water', 'value': False},
            {'name': 'boiler', 'value': False},
            {'name': 'washing_machine', 'value': 'off'}
        ]
        post_data = post_data + data
        # need send_mail.
        send_mail('Leak detector', 'Leak detector was activated', settings.EMAIL_HOST_USER, [settings.EMAIL_RECEPIENT])

    # 2 условие
    if not cur_conditions['cold_water'] and (cur_conditions['boiler'] or cur_conditions['washing_machine'] == 'on'):
        data = [{'name': 'boiler', 'value': False}, {'name': 'washing_machine', 'value': 'off'}]
        post_data = post_data + data

    # 3 условие с учетом выполнения второго и шестого
    water_t = Setting.objects.get(controller_name='hot_water_target_temperature')
    if cur_conditions['boiler_temperature'] \
            and cur_conditions['boiler_temperature'] < 0.9 * water_t.value \
            and cur_conditions['cold_water'] \
            and not cur_conditions['smoke_detector'] and not cur_conditions['leak_detector'] \
            and not cur_conditions['boiler']:
        data = [{'name': 'boiler', 'value': True}]
        post_data = post_data + data

    if cur_conditions['boiler_temperature'] \
            and cur_conditions['boiler_temperature'] > 1.1 * water_t.value \
            and cur_conditions['boiler']:
        data = [{'name': 'boiler', 'value': False}]
        post_data = post_data + data

    # 4 + 5 условия
    if cur_conditions['curtains'] == 'slightly_open':
        pass
    elif cur_conditions['outdoor_light'] < 50 \
            and not cur_conditions['bedroom_light'] \
            and not cur_conditions['curtains'] == 'open':
        data = [{'name': 'curtains', 'value': 'open'}]
        post_data = post_data + data
    elif (cur_conditions['outdoor_light'] > 50 or cur_conditions['bedroom_light']) \
            and cur_conditions['curtains'] == 'open':
        data = [{'name': 'curtains', 'value': 'close'}]
        post_data = post_data + data

    # 6 условие
    if cur_conditions['smoke_detector'] and (
            cur_conditions['air_conditioner']
            or cur_conditions['bedroom_light']
            or cur_conditions['bathroom_light']
            or cur_conditions['boiler']
            or cur_conditions['washing_machine'] == 'on'
    ):
        data = [
            {'name': 'air_conditioner', 'value': False},
            {'name': 'bedroom_light', 'value': False},
            {'name': 'bathroom_light', 'value': False},
            {'name': 'boiler', 'value': False},
            {'name': 'washing_machine', 'value': 'off'}
        ]
        post_data = post_data + data

    # 7 условие
    bedroom_t = Setting.objects.get(controller_name='bedroom_target_temperature')
    if cur_conditions['bedroom_temperature'] > 1.1 * bedroom_t.value and not cur_conditions['smoke_detector'] and not \
            cur_conditions['air_conditioner']:
        data = [{'name': 'air_conditioner', 'value': True}]
        post_data = post_data + data

    elif cur_conditions['bedroom_temperature'] < 0.9 * bedroom_t.value and cur_conditions['air_conditioner']:
        data = [{'name': 'air_conditioner', 'value': False}]
        post_data = post_data + data

    if bool(post_data):
        send_post_data = []
        duplicates = set()
        for d in post_data:
            t = tuple(d.items())
            if t not in duplicates:
                duplicates.add(t)
                send_post_data.append(d)
        # print('Hi')
        # print(send_post_data)
        post_request(send_post_data)
