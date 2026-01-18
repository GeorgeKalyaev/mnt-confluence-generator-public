"""Интеграция с Confluence API"""
import httpx
from typing import Optional, Dict, Any, List
from app.config import settings
import base64
import json
import io
import logging

logger = logging.getLogger("mnt_generator.confluence")


class ConfluenceClient:
    """Клиент для работы с Confluence API"""
    
    def __init__(self):
        self.base_url = settings.confluence_url.rstrip('/')
        self.auth = self._get_auth()
    
    def _get_auth(self) -> tuple:
        """Получение данных для аутентификации"""
        if settings.confluence_email and settings.confluence_api_token:
            # Cloud: Basic auth с email и API token
            credentials = f"{settings.confluence_email}:{settings.confluence_api_token}"
            encoded = base64.b64encode(credentials.encode()).decode()
            return ("Authorization", f"Basic {encoded}")
        elif settings.confluence_username and settings.confluence_password:
            # Server/Datacenter: Basic auth с username и password
            credentials = f"{settings.confluence_username}:{settings.confluence_password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            return ("Authorization", f"Basic {encoded}")
        else:
            raise ValueError("Confluence credentials not configured")
    
    async def create_page(
        self,
        space_key: str,
        title: str,
        content: str,
        parent_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Создание страницы в Confluence
        
        Args:
            space_key: Ключ пространства
            title: Заголовок страницы
            content: Контент в Storage Format
            parent_id: ID родительской страницы (опционально)
        
        Returns:
            Словарь с информацией о созданной странице
        """
        url = f"{self.base_url}/rest/api/content"
        
        body = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }
        
        if parent_id:
            body["ancestors"] = [{"id": parent_id}]
        
        headers = {
            "Content-Type": "application/json",
            self.auth[0]: self.auth[1]
        }
        
        async with httpx.AsyncClient() as client:
            logger.debug(f"Отправляем POST запрос на {url}")
            logger.debug(f"body keys = {list(body.keys())}, space_key = {space_key}, title = {title[:50]}...")
            response = await client.post(url, json=body, headers=headers, timeout=30.0)
            logger.debug(f"Получен ответ со статусом {response.status_code}")
            
            if response.status_code != 200 and response.status_code != 201:
                error_text = response.text
                error_message = f"Ошибка Confluence API (код {response.status_code})"
                
                try:
                    error_json = response.json()
                    # Извлекаем понятное сообщение об ошибке
                    if isinstance(error_json, dict):
                        if "message" in error_json:
                            error_message = error_json["message"]
                        elif "data" in error_json and isinstance(error_json["data"], dict):
                            if "errors" in error_json["data"]:
                                errors = error_json["data"]["errors"]
                                if isinstance(errors, list) and len(errors) > 0:
                                    error_message = errors[0].get("message", error_message)
                        error_text = str(error_json)
                except:
                    pass
                
                # Формируем понятное сообщение для пользователя
                if response.status_code == 400:
                    user_message = f"Неверный запрос к Confluence: {error_message}. Проверьте корректность Space Key, Parent Page ID и других параметров."
                elif response.status_code == 401:
                    user_message = "Ошибка аутентификации в Confluence. Проверьте правильность email/token или username/password в настройках."
                elif response.status_code == 403:
                    user_message = "Нет прав доступа к Confluence. Убедитесь, что у вас есть права на создание страниц в указанном пространстве."
                elif response.status_code == 404:
                    user_message = "Ресурс не найден в Confluence. Проверьте корректность Space Key и Parent Page ID."
                elif response.status_code == 409:
                    user_message = "Конфликт в Confluence. Возможно, страница с таким названием уже существует."
                elif response.status_code >= 500:
                    user_message = f"Ошибка сервера Confluence (код {response.status_code}). Попробуйте позже или обратитесь к администратору Confluence."
                else:
                    user_message = f"Ошибка при обращении к Confluence (код {response.status_code}): {error_message}"
                
                logger.error(f"Confluence API ОШИБКА - {response.status_code}: {error_text}")
                raise Exception(user_message)
            
            logger.debug("Страница успешно создана")
            
            result = response.json()
            
            # Формируем URL страницы
            page_url = f"{self.base_url}/pages/viewpage.action?pageId={result['id']}"
            
            return {
                "id": result["id"],
                "url": page_url,
                "title": result["title"]
            }
    
    async def update_page(
        self,
        page_id: int,
        title: str,
        content: str,
        version: int
    ) -> Dict[str, Any]:
        """
        Обновление страницы в Confluence
        
        Args:
            page_id: ID страницы
            title: Заголовок страницы
            content: Контент в Storage Format
            version: Текущая версия страницы (будет увеличена на 1)
        
        Returns:
            Словарь с информацией об обновленной странице
        """
        url = f"{self.base_url}/rest/api/content/{page_id}"
        
        body = {
            "version": {"number": version + 1},
            "title": title,
            "type": "page",
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            self.auth[0]: self.auth[1]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.put(url, json=body, headers=headers, timeout=30.0)
            
            if response.status_code != 200 and response.status_code != 201:
                error_text = response.text
                error_message = f"Ошибка Confluence API (код {response.status_code})"
                
                try:
                    error_json = response.json()
                    if isinstance(error_json, dict):
                        if "message" in error_json:
                            error_message = error_json["message"]
                        elif "data" in error_json and isinstance(error_json["data"], dict):
                            if "errors" in error_json["data"]:
                                errors = error_json["data"]["errors"]
                                if isinstance(errors, list) and len(errors) > 0:
                                    error_message = errors[0].get("message", error_message)
                except:
                    pass
                
                if response.status_code == 409:
                    user_message = "Конфликт версий в Confluence. Страница была изменена другим пользователем. Обновите страницу и попробуйте снова."
                elif response.status_code == 404:
                    user_message = "Страница не найдена в Confluence. Возможно, она была удалена."
                elif response.status_code == 403:
                    user_message = "Нет прав на обновление страницы в Confluence."
                else:
                    user_message = f"Ошибка обновления страницы в Confluence (код {response.status_code}): {error_message}"
                
                logger.error(f"Confluence API ОШИБКА при обновлении - {response.status_code}: {error_text}")
                raise Exception(user_message)
            
            result = response.json()
            
            # Формируем URL страницы
            page_url = f"{self.base_url}/pages/viewpage.action?pageId={result['id']}"
            
            return {
                "id": result["id"],
                "url": page_url,
                "title": result["title"],
                "version": result["version"]["number"]
            }
    
    async def get_page(self, page_id: int, expand: str = "version") -> Dict[str, Any]:
        """
        Получение информации о странице (включая версию)
        
        Args:
            page_id: ID страницы
            expand: Какие поля расширять (version, body.storage, etc.)
        
        Returns:
            Словарь с информацией о странице
        """
        url = f"{self.base_url}/rest/api/content/{page_id}?expand={expand}"
        
        headers = {
            self.auth[0]: self.auth[1]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            return response.json()
    
    async def get_page_content(self, page_id: int) -> Optional[str]:
        """
        Получение содержимого страницы в формате Storage
        
        Args:
            page_id: ID страницы
        
        Returns:
            Содержимое страницы в формате Storage или None при ошибке
        """
        try:
            page_data = await self.get_page(page_id, expand="version,body.storage")
            body = page_data.get("body", {})
            storage = body.get("storage", {})
            return storage.get("value", "")
        except Exception as e:
            logger.error(f"Ошибка получения содержимого страницы {page_id}: {e}")
            return None
    
    async def get_page_version_info(self, page_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение информации о версии страницы
        
        Args:
            page_id: ID страницы
        
        Returns:
            Словарь с информацией о версии: {number, when, friendlyWhen, message, by} или None
        """
        try:
            page_data = await self.get_page(page_id, expand="version")
            version_info = page_data.get("version", {})
            return version_info
        except Exception as e:
            logger.error(f"Ошибка получения версии страницы {page_id}: {e}")
            return None
    
    async def upload_attachment(
        self,
        page_id: int,
        filename: str,
        file_content: bytes,
        content_type: str = "image/png"
    ) -> Dict[str, Any]:
        """
        Загрузка вложения (изображения) на страницу Confluence
        
        Args:
            page_id: ID страницы
            filename: Имя файла
            file_content: Содержимое файла (bytes)
            content_type: MIME тип файла
        
        Returns:
            Словарь с информацией о загруженном вложении
        """
        url = f"{self.base_url}/rest/api/content/{page_id}/child/attachment"
        
        # Подготавливаем multipart/form-data
        files = {
            "file": (filename, io.BytesIO(file_content), content_type)
        }
        
        data = {
            "comment": "Uploaded from MNT Generator"
        }
        
        headers = {
            self.auth[0]: self.auth[1],
            "X-Atlassian-Token": "no-check"  # Требуется для загрузки файлов
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=60.0  # Увеличено для больших файлов
            )
            
            if response.status_code != 200 and response.status_code != 201:
                error_text = response.text
                try:
                    error_json = response.json()
                    error_text = str(error_json)
                except:
                    pass
                raise Exception(f"Confluence API error {response.status_code}: {error_text}")
            
            result = response.json()
            
            # Получаем информацию о загруженном файле
            attachments = result.get("results", [])
            if attachments:
                attachment = attachments[0]
                download_url = attachment.get("_links", {}).get("download", "")
                return {
                    "id": attachment.get("id"),
                    "filename": attachment.get("title"),
                    "download_url": download_url if download_url.startswith("http") else f"{self.base_url}{download_url}"
                }
            
            raise Exception("Failed to upload attachment")
    
    async def get_attachments(self, page_id: int) -> List[Dict[str, Any]]:
        """
        Получение списка вложений страницы
        
        Args:
            page_id: ID страницы
        
        Returns:
            Список вложений
        """
        url = f"{self.base_url}/rest/api/content/{page_id}/child/attachment"
        
        headers = {
            self.auth[0]: self.auth[1]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            result = response.json()
            attachments = result.get("results", [])
            
            # Возвращаем упрощенный список с нужной информацией
            return [
                {
                    "id": att.get("id"),
                    "filename": att.get("title"),
                    "mediaType": att.get("mediaType"),
                    "fileSize": att.get("fileSize"),
                    "downloadUrl": att.get("_links", {}).get("download", "")
                }
                for att in attachments
            ]
    
    async def delete_page(self, page_id: int) -> None:
        """
        Удаление страницы из Confluence
        
        Args:
            page_id: ID страницы для удаления
        """
        url = f"{self.base_url}/rest/api/content/{page_id}"
        
        headers = {
            self.auth[0]: self.auth[1]
        }
        
        async with httpx.AsyncClient() as client:
            logger.debug(f"Удаление страницы {page_id} из Confluence")
            response = await client.delete(url, headers=headers, timeout=30.0)
            
            if response.status_code == 204:
                logger.info(f"Страница {page_id} успешно удалена из Confluence")
            elif response.status_code == 404:
                logger.warning(f"Страница {page_id} не найдена в Confluence (возможно, уже удалена)")
            else:
                error_message = f"Ошибка удаления страницы {page_id} из Confluence (код {response.status_code})"
                try:
                    error_json = response.json()
                    if isinstance(error_json, dict) and "message" in error_json:
                        error_message = error_json["message"]
                except:
                    pass
                logger.error(f"{error_message}: {response.text}")
                response.raise_for_status()
    
    async def delete_attachment(self, page_id: int, attachment_id: int) -> None:
        """
        Удаление вложения со страницы
        
        Args:
            page_id: ID страницы (не используется в API, но оставлен для совместимости)
            attachment_id: ID вложения
        """
        # В Confluence API вложения удаляются напрямую через их ID как обычный контент
        url = f"{self.base_url}/rest/api/content/{attachment_id}"
        
        headers = {
            self.auth[0]: self.auth[1]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=headers, timeout=30.0)
            response.raise_for_status()


def get_confluence_client() -> ConfluenceClient:
    """Получение клиента Confluence"""
    return ConfluenceClient()


def is_confluence_configured() -> bool:
    """Проверка наличия настроек Confluence"""
    try:
        # Проверяем наличие credentials без создания клиента
        has_cloud_creds = bool(settings.confluence_email and settings.confluence_api_token)
        has_server_creds = bool(settings.confluence_username and settings.confluence_password)
        return has_cloud_creds or has_server_creds
    except Exception:
        return False
