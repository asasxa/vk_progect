import json
import os
from datetime import datetime
import requests
from dotenv import load_dotenv
from tqdm import tqdm  

dotenv_path = 'config.env'

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

VK_TOKEN = os.getenv('VK_TOKEN')
YA_TOKEN = os.getenv('YA_TOKEN')

class VKConnector:
    def __init__(self, access_token, version=5.199):
        self.access_token = access_token
        self.version = version
        self.base_url = 'https://api.vk.com/method/'
        self.params = {
            'access_token': self.access_token,
            'v': self.version
        }

    def photos_info(self, owner_id, count=5, extended=1, photo_sizes=1):
        url = f'{self.base_url}photos.get'
        params = {
            **self.params,
            'owner_id': owner_id,
            'album_id': 'profile',
            'count': count,
            'extended': extended,
            'photo_sizes': photo_sizes
        }
        response = requests.get(url, params=params)
        return response.json()

class YAConnector:
    def __init__(self, token):
        self.headers = {'Authorization': f'OAuth {token}'}

    def create_folder(self, folder_name):
        url_create_folder = 'https://cloud-api.yandex.net/v1/disk/resources'
        response = requests.put(url=url_create_folder, 
                                headers=self.headers, 
                                params={'path': folder_name})
        return response.status_code
    
    def upload_image(self, image_name, photo_url):
        url_upload_image = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        response = requests.post(url=url_upload_image,
                                 headers=self.headers,
                                 params={'path': f'/{FOLDER_NAME}/{image_name}',
                                         'url': photo_url,
                                        })
        return response.status_code                        

FOLDER_NAME = 'VK_photo_loaded'
vk_connector = VKConnector(VK_TOKEN)
photos_info = vk_connector.photos_info(83773123)

ya_connector = YAConnector(YA_TOKEN)
ya_connector.create_folder(FOLDER_NAME)

photo_info_json = []
image_name_dict = {}
likes_check_dict = {}

total_photos = len(photos_info['response']['items'])
total_uploads = total_photos
total_file_writes = 1  
total_operations = total_photos + total_uploads + total_file_writes

with tqdm(total=100, desc="Прогресс", unit="операций") as pbar:
    for item in photos_info['response']['items']:
        likes_count = item['likes']['count']
        date = item['date']
        date_str = datetime.fromtimestamp(date).strftime('%Y-%m-%d_%H-%M-%S')

        if likes_count not in likes_check_dict:
            image_name = f'{likes_count}.jpg'
        else:
            image_name = f'{likes_count}-{date_str}.jpg'
        likes_check_dict[likes_count] = 1

        image_sizes = item['sizes']
        best_image = None
        max_height =  0
        max_width =  0

        for image in image_sizes:
            if (image['height'] > max_height) and (image['width'] > max_width):
                max_height = image['height']
                max_width = image['width']
                best_image = image
        
        if best_image:
            image_name_dict[image_name] = best_image['url']
        else:
            image_name_dict[image_name] = 'Нет подходящего разрешения'

        photo_info_json.append({
            "file_name": f"{image_name}",
            "size": f"{best_image['type']}"
        })

        pbar.update(1 * 100 / total_operations)  

    for image_name, photo_url in image_name_dict.items(): 
        ya_connector.upload_image(image_name, photo_url)
        pbar.update(1 * 100 / total_operations) 

    with open('photo_info.json', 'w') as file:
        json.dump(photo_info_json, file, ensure_ascii=False, indent=0)
    
    pbar.update(1 * 100 / total_operations)