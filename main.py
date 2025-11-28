import requests
import json
import os
from tqdm import tqdm
from datetime import datetime


class CatBackup:
    def __init__(self, yandex_token):
        """
        Инициализация класса для резервного копирования
        
        :param yandex_token: Токен Яндекс.Диска
        """
        self.yandex_token = yandex_token
        self.yandex_base_url = "https://cloud-api.yandex.net/v1/disk/resources"
        self.headers = {
            'Authorization': f'OAuth {self.yandex_token}',
            'Content-Type': 'application/json'
        }
        
    def get_cat_image(self, text):
        """
        Получение картинки кота с текстом от cataas.com
        
        :param text: Текст для наложения на картинку
        :return: bytes content картинки или None при ошибке
        """
        try:
            url = f"https://cataas.com/cat/says/{text}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении картинки: {e}")
            return None
    
    def create_folder(self, folder_name):
        """
        Создание папки на Яндекс.Диске
        
        :param folder_name: Название папки (название группы)
        :return: True если успешно, False если ошибка
        """
        try:
            response = requests.put(
                f"{self.yandex_base_url}?path={folder_name}",
                headers=self.headers
            )
            
            # Папка уже существует - это не ошибка
            if response.status_code in [201, 409]:
                print(f"Папка '{folder_name}' готова на Яндекс.Диске")
                return True
            else:
                print(f"Ошибка создания папки: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при создании папки: {e}")
            return False
    
    def upload_to_yandex(self, folder_name, file_name, image_content):
        """
        Загрузка картинки на Яндекс.Диск
        
        :param folder_name: Название папки
        :param file_name: Название файла
        :param image_content: Содержимое картинки
        :return: Информация о загруженном файле или None при ошибке
        """
        try:
            # Получаем URL для загрузки
            upload_response = requests.get(
                f"{self.yandex_base_url}/upload?path={folder_name}/{file_name}.jpg&overwrite=true",
                headers=self.headers
            )
            upload_data = upload_response.json()
            
            if 'href' not in upload_data:
                print(f"Ошибка получения URL для загрузки: {upload_data}")
                return None
            
            # Загружаем файл
            upload_url = upload_data['href']
            put_response = requests.put(upload_url, data=image_content)
            
            if put_response.status_code == 201:
                # Получаем информацию о файле
                file_info_response = requests.get(
                    f"{self.yandex_base_url}?path={folder_name}/{file_name}.jpg",
                    headers=self.headers
                )
                
                if file_info_response.status_code == 200:
                    file_info = file_info_response.json()
                    return {
                        'file_name': f"{file_name}.jpg",
                        'size': file_info.get('size', 0),
                        'created': datetime.now().isoformat(),
                        'path': file_info.get('path', '')
                    }
            
            print(f"Ошибка загрузки файла: {put_response.status_code}")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при загрузке на Яндекс.Диск: {e}")
            return None
    
    def save_to_json(self, data, filename="backup_info.json"):
        """
        Сохранение информации в JSON файл
        
        :param data: Данные для сохранения
        :param filename: Имя файла
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Информация сохранена в файл: {filename}")
        except Exception as e:
            print(f"Ошибка при сохранении JSON: {e}")
    
    def backup_cats(self, text, group_name):
        """
        Основная функция резервного копирования
        
        :param text: Текст для картинки
        :param group_name: Название группы (папки)
        """
        print(f"Начинаем резервное копирование картинки с текстом: '{text}'")
        
        # Создаем папку на Яндекс.Диске
        if not self.create_folder(group_name):
            return
        
        # Получаем картинку
        print("Получаем картинку с cataas.com...")
        image_content = self.get_cat_image(text)
        
        if not image_content:
            print("Не удалось получить картинку")
            return
        
        # Загружаем на Яндекс.Диск
        print("Загружаем на Яндекс.Диск...")
        file_info = self.upload_to_yandex(group_name, text, image_content)
        
        if file_info:
            # Сохраняем информацию в JSON
            backup_data = {
                'backup_info': {
                    'timestamp': datetime.now().isoformat(),
                    'text': text,
                    'group_name': group_name,
                    'files': [file_info]
                }
            }
            
            self.save_to_json(backup_data)
            print("Резервное копирование завершено успешно!")
            print(f"Размер загруженного файла: {file_info['size']} байт")
        else:
            print("Резервное копирование завершено с ошибками")


def main():
    """
    Основная функция программы
    """
    print("=== Программа резервного копирования картинок с котами ===")
    
    # Получаем данные от пользователя
    text = input("Введите текст для картинки: ").strip()
    yandex_token = input("Введите токен Яндекс.Диска: ").strip()
    group_name = input("Введите название вашей группы в Нетологии: ").strip()
    
    if not text or not yandex_token or not group_name:
        print("Ошибка: Все поля должны быть заполнены!")
        return
    
    # Создаем экземпляр класса и запускаем резервное копирование
    backup = CatBackup(yandex_token)
    backup.backup_cats(text, group_name)


if __name__ == "__main__":
    main()