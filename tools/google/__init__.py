from googleapiclient.discovery import build
from .auth import get_google_credentials


def get_google_service(service_name: str, version: str, scopes: list):
    """Cria serviço Google compartilhado com tratamento de erro.

    Args:
        service_name: 'drive', 'calendar', 'gmail'
        version: 'v3', 'v3', 'v1'
        scopes: lista de scopes OAuth

    Returns:
        Resource do Google API

    Raises:
        ValueError se credenciais não encontradas
        Exception se API indisponível
    """
    creds = get_google_credentials(scopes)
    if creds is None:
        raise ValueError(f"Google {service_name}: credenciais não encontradas. Verificar GOOGLE_TOKEN_PATH no .env")
    return build(service_name, version, credentials=creds)


def test_connection(service_name: str = "drive", version: str = "v3",
                     scopes: list = None) -> bool:
    """Testa conexão com Google API."""
    if scopes is None:
        scopes = ["https://www.googleapis.com/auth/drive"]

    try:
        get_google_service(service_name, version, scopes)
        return True
    except Exception as e:
        print(f"  Google {service_name} falhou: {e}")
        return False