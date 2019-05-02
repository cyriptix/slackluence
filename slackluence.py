import glob
import html
import json
import oauthlib
import os
import re
import requests
from requests_oauthlib import OAuth1Session
import sys
import time

slack_oauth_token = ''
channels_to_export = ['']
working_dir = ''

confluence_baseurl = ''
confluence_space = ''
confluence_token = ''
confluence_key = open('').read()
confluence_consumer = ''

def download_attachments(message):
    for file in message['files']:
        if file['mode'] != 'tombstone':
            filename = '{}.{}'.format(file['id'], file['filetype'])
            existing_files = glob.glob('attachments/*')
            if 'attachments/{}'.format(filename) not in existing_files:
                payload = {'token': slack_oauth_token}
                r = requests.get(file['url_private_download'], params=payload)
                with open('attachments/{}'.format(filename), 'ab') as f:
                    f.write(r.content)

def create_empty_confluence_page(page_title):
    payload = { 
        'type': 'page', 
        'title': page_title, 
        'space': { 
            'key': confluence_space
        },
        'body': {
        }
    }
    oauth = OAuth1Session(confluence_consumer, 
                          signature_method=oauthlib.oauth1.SIGNATURE_RSA,
                          resource_owner_key=confluence_token,
                          signature_type='query',
                          rsa_key=confluence_key)
    r = oauth.post('{}/rest/api/content'.format(confluence_baseurl),
                   data=json.dumps(payload),
                   headers={
                       'X-Atlassian-Token': 'no-check',
                       'Content-Type': 'application/json'
                   })
    return r.json()['id']

def update_confluence_page(confluence_space, page_id, channel, content):
    payload = {
        "id": page_id,
        "type": "page",
        "title": channel,
        "space": {
            "key": confluence_space
        },
        "body": {
            "storage": {
                "value": content,
                "representation": "storage"
            }
        },
        "version": {
            "number": 2
        }
    }
    oauth = OAuth1Session(confluence_consumer, 
                          signature_method=oauthlib.oauth1.SIGNATURE_RSA,
                          resource_owner_key=confluence_token,
                          signature_type='query',
                          rsa_key=confluence_key)
    r = oauth.put('{}/rest/api/content/{}'.format(confluence_baseurl, page_id),
                   data=json.dumps(payload),
                   headers={
                       'X-Atlassian-Token': 'no-check',
                       'Content-Type': 'application/json'
                   })
    print(r)

def attach_avatar_to_page(page_id, attachment_id):
    file = {'file': open(glob.glob('avatars/{}*'.format(attachment_id))[0], 'rb')}
    oauth = OAuth1Session(confluence_consumer,
                          signature_method=oauthlib.oauth1.SIGNATURE_RSA,
                          resource_owner_key=confluence_token,
                          signature_type='query',
                          rsa_key=confluence_key)
    r = oauth.post('{}/rest/api/content/{}/child/attachment'.format(confluence_baseurl, page_id),
                   files=file,
                   headers={
                       'X-Atlassian-Token': 'no-check'
                   })

def attach_file_to_page(page_id, attachment_id, title):
    file = {'file': (title, open(glob.glob('attachments/{}*'.format(attachment_id))[0], 'rb'))}
    oauth = OAuth1Session(confluence_consumer,
                          signature_method=oauthlib.oauth1.SIGNATURE_RSA,
                          resource_owner_key=confluence_token,
                          signature_type='query',
                          rsa_key=confluence_key)
    r = oauth.post('{}/rest/api/content/{}/child/attachment'.format(confluence_baseurl, page_id),
                   files=file,
                   headers={
                       'X-Atlassian-Token': 'no-check'
                   })

def get_all_users():
    payload = {'token': slack_oauth_token}
    user_dict = {}
    r = requests.get('https://slack.com/api/users.list', params=payload)
    for member in r.json()['members']:
        user_dict[member['id']] = {}
        user_dict[member['id']]['name'] = member['profile']['real_name']
        user_dict[member['id']]['avatar'] = member['profile']['image_72']
    return user_dict

def get_channel_users(channel):
    channel_user_list = []
    channel_dir = '{}/{}'.format(working_dir, channel)
    for inputfile in glob.glob('{}/*.json'.format(channel_dir)):
        with open(inputfile) as f:
            for message in json.loads(f.read()):
                if 'subtype' not in message:
                    channel_user_list.append(message['user'])
    return set(channel_user_list)

def download_avatars(user_list):
    existing_files = glob.glob('avatars/*')
    for user in user_list:
        if 'avatars/{}.jpg'.format(user) not in existing_files:
            r = requests.get(user_list[user]['avatar'])
            with open('avatars/{}.jpg'.format(user), 'ab') as f:
                f.write(r.content)

def fix_slack_formatting(text):
    user_mentions = re.findall('<@[A-Z0-9]{9}>', text)
    for mention in user_mentions:
        id = mention.translate({ord(i): None for i in '<@>'})
        text = text.replace(mention, '@{}'.format(full_user_list[id]['name']))
    links = re.findall('<http.*>', text)
    for link in links:
        text = text.replace(link, link.translate({ord(i): None for i in '<>'}).split('|')[0])
    channels = re.findall('<#[A-Z0-9]{9}.*>', text)
    for channel in channels:
        text = text.replace(channel, '#{}'.format(channel.translate({ord(i): None for i in '<>'}).split('|')[1]))
    return html.escape(text)

def build_row_from_message(message):
    avatar = '{}.jpg'.format(message['user'])
    username = full_user_list[message['user']]['name']
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(message['ts'])))
    content = fix_slack_formatting(message['text'])
    row = '<tr> \
           <td><p><ac:image><ri:attachment ri:filename="{}"/></ac:image></p></td> \
           <td><p><b>{}</b>&nbsp;&nbsp;{}</p><p>{}</p>'.format(avatar, username, timestamp, content)
    if 'files' in message:
        for file in message['files']:
            if file['mode'] != 'tombstone':
                file_data = '<p><ac:link><ri:attachment ri:filename="{}"/></ac:link></p>'.format(file['title'])
                print(file_data)
                row += file_data
                print(row)
    row += '</td></tr>'
    return(row)

for folder in 'avatars', 'attachments':
    if not os.path.exists(folder):
        os.makedirs(folder)
full_user_list = get_all_users()
download_avatars(get_all_users())

for channel in channels_to_export:
    page_body = '<table>'
    channel_dir = '{}/{}'.format(working_dir, channel)
    channel_user_list = get_channel_users(channel)
    page_id = create_empty_confluence_page('{}-test'.format(channel))
    for user in channel_user_list:
        attach_avatar_to_page(page_id, user)
    for inputfile in glob.glob('{}/*.json'.format(channel_dir)):
        with open(inputfile) as f:
            for message in json.loads(f.read()):
                if 'files' in message:
                    download_attachments(message)
                    for file in message['files']:
                        if file['mode'] != 'tombstone':
                            attach_file_to_page(page_id, file['id'], file['title'])
                if 'subtype' not in message:
                    row = build_row_from_message(message)
                    page_body += row
    page_body += '</table>'
    update_confluence_page(confluence_space, page_id, channel, page_body)
            

