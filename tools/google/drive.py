from googleapiclient.http import MediaFileUpload
from . import get_google_service

SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_service():
    return get_google_service("drive", "v3", SCOPES)


def list_files(limit=10):
    """Lista arquivos recentes no Drive."""
    try:
        service = get_service()
        results = service.files().list(
            pageSize=limit,
            fields="files(id, name, mimeType)"
        ).execute()
        return [{"name": f["name"], "type": f["mimeType"]} for f in results.get('files', [])]
    except Exception as e:
        return {"error": str(e), "cause": "Drive API falhou"}


def search_file(name):
    """Busca arquivo por nome."""
    try:
        service = get_service()
        results = service.files().list(
            q=f"name contains '{name}'",
            fields="files(id, name)"
        ).execute()
        return results.get('files', [])
    except Exception as e:
        return {"error": str(e), "cause": "Drive API falhou"}


def create_folder(name):
    """Cria pasta no Drive."""
    try:
        service = get_service()
        file_metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
        return service.files().create(body=file_metadata, fields='id').execute()
    except Exception as e:
        return {"error": str(e), "cause": "Drive API falhou"}


def upload_file(file_path, file_name, folder_id=None):
    """Faz upload de arquivo. Opcionalmente dentro de uma pasta."""
    try:
        service = get_service()
        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        media = MediaFileUpload(file_path)
        return service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    except Exception as e:
        return {"error": str(e), "cause": "Drive API falhou"}


def delete_file(file_id):
    """Deleta arquivo por ID."""
    try:
        service = get_service()
        service.files().delete(fileId=file_id).execute()
        return {"status": "deleted", "file_id": file_id}
    except Exception as e:
        return {"error": str(e), "cause": "Drive API falhou"}