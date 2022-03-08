import os

import pydub
import random
import requests
import vk_api
from flask import Flask, request, json

from _token import token
from speech_recognition_engine import recognition

app = Flask(__name__)


@app.route('/', methods=['POST'])
def processing():
    urls = []
    data = json.loads(request.data)
    event_id = str(data['event_id'])
    with open('mysite/data.log', 'r', encoding='utf-8') as file:
        for num, line in enumerate(file):
            if str(event_id) == line[:-1]:
                return 'ok'
    if 'type' not in data.keys():
        return 'not vk'
    if data['type'] == 'confirmation':
        return 'd5f22bde'
    elif data['type'] == 'message_new':
        peer_id = data['object']['peer_id']
        if data['object']['attachments']:
            if data['object']['attachments'][0]['type'] == 'audio_message':
                urls.append(data['object']['attachments'][0]['audio_message']['link_mp3'])
        elif data['object']['fwd_messages']:
            fwd_messages = data['object']['fwd_messages']
            for fwd_message in fwd_messages:
                if fwd_message['attachments']:
                    if fwd_message['attachments'][0]['type'] == 'audio_message':
                        urls.append(fwd_message['attachments'][0]['audio_message']['link_mp3'])

        save_data(event_id)
        speech_recognition(urls, peer_id)
        return 'ok'


def save_data(data):
    path = 'mysite/data.log'
    if int(os.path.getsize(path)) > 1000:
        with open(path, 'w', encoding='utf-8') as out_file:
            log_line = f'{data}\n'
            out_file.write(log_line)
    else:
        with open(path, 'a', encoding='utf-8') as out_file:
            log_line = f'{data}\n'
            out_file.write(log_line)


def audio_download(urls):
    urls = urls
    for url_num, url in enumerate(urls):
        mp3_file = requests.get(url)
        mp3_file_path = os.path.join("mp3_audio", f'message{url_num}.mp3')
        with open(mp3_file_path, 'wb') as save_file:
            save_file.write(mp3_file.content)
        wav_file = pydub.AudioSegment.from_mp3(mp3_file_path)
        wav_file.export(os.path.join("audio", f'message{url_num}.wav'), format="wav")
        os.remove(mp3_file_path)


def speech_recognition(urls, peer_id):
    audio_download(urls)
    reply_messages = []
    path_normalized = os.path.normpath('audio')
    for dirpath, _, filenames in os.walk(path_normalized):
        for file in filenames:
            full_file_path = os.path.join(dirpath, file)
            recognited_message = recognition(full_file_path)
            if recognited_message:
                reply_messages.append(recognited_message)
            else:
                reply_messages.append('Ничего не разобрать')
            os.remove(full_file_path)
    if reply_messages:
        with open('mysite/messages.log', 'a', encoding='utf-8') as out_file:
            log_line = f'PEER_ID: {str(peer_id)}, MESSAGE:{str(reply_messages)}\n'
            out_file.write(log_line)
    reply_to_user(peer_id, reply_messages)


def reply_to_user(peer_id, reply_messages):
    session = vk_api.VkApi(token=token)
    api = session.get_api()
    for reply_message in reply_messages:
        api.messages.send(
            message=reply_message,
            random_id=random.randint(0, 2 ** 20),
            peer_id=peer_id
        )
