import os
import json
from google.oauth2.credentials import Credentials


def get_google_credentials(scopes):
    """Retorna credenciais Google OAuth.

    Lê token de GOOGLE_TOKEN_PATH (env var obrigatória).
    Suporta expansão de ~ e variáveis de ambiente no path.

    Returns:
        Credentials ou None se token não encontrado
    """
    token_path = os.environ.get("GOOGLE_TOKEN_PATH")

    if not token_path:
        return None

    token_path = os.path.expandvars(os.path.expanduser(token_path))

    try:
        with open(token_path, "r") as f:
            creds_data = json.load(f)
    except FileNotFoundError:
        print(f"  Google: token não encontrado em {token_path}")
        return None
    except json.JSONDecodeError:
        print(f"  Google: token inválido em {token_path}")
        return None

    return Credentials.from_authorized_user_info(creds_data, scopes)