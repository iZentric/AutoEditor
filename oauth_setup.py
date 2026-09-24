"""Local-PC OAuth setup. Browser consent -> GitHub Secrets, without printing tokens."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
AUTH_ENDPOINTS = {'https://accounts.google.com/o/oauth2/auth',
                  'https://accounts.google.com/o/oauth2/v2/auth'}
TOKEN_ENDPOINTS = {'https://oauth2.googleapis.com/token',
                   'https://accounts.google.com/o/oauth2/token'}


class SetupError(Exception):
    """Controlled messages only; never put credentials or provider error bodies here."""


def load_client(path):
    try:
        configuration = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise SetupError('Lipseste client_secret.json valid, descarcat pentru clientul OAuth Desktop.') from None
    installed = configuration.get('installed') if isinstance(configuration, dict) else None
    if not isinstance(installed, dict):
        raise SetupError('Clientul trebuie sa fie Desktop app, nu Web application.')
    if (installed.get('auth_uri') not in AUTH_ENDPOINTS
            or installed.get('token_uri') not in TOKEN_ENDPOINTS):
        raise SetupError('Fisier respins: endpoint-urile nu sunt cele oficiale Google.')
    identifier, secret = installed.get('client_id'), installed.get('client_secret')
    if (not isinstance(identifier, str) or not identifier.endswith('.apps.googleusercontent.com')
            or not isinstance(secret, str) or not secret.strip()):
        raise SetupError('Clientul OAuth nu contine identificatorul si secretul necesare.')
    return {'installed': installed}


def gh_call(arguments, secret_input=None):
    result = subprocess.run(['gh', *arguments], input=secret_input, text=True,
                            capture_output=True, timeout=90)
    if result.returncode:
        # gh errors/tracebacks may include request information. Do not echo them.
        raise SetupError('GitHub a refuzat operatia. Verifica autentificarea si accesul la repository/Secrets/Variables.')
    return result.stdout


def check_github(repo):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise SetupError('Repository invalid: foloseste formatul proprietar/nume.')
    if not shutil.which('gh'):
        raise SetupError('Instaleaza GitHub CLI de la cli.github.com, apoi ruleaza gh auth login --web.')
    gh_call(['auth', 'status', '--hostname', 'github.com'])
    gh_call(['secret', 'list', '--repo', repo])


def authorize(configuration):
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        raise SetupError('Instaleaza dependinta: python -m pip install -r requirements-oauth.txt') from None
    flow = InstalledAppFlow.from_client_config(configuration, SCOPES,
                                               autogenerate_code_verifier=True)
    # Loopback is intentional: this script runs on the user's own PC, never in Arena/CI.
    return flow.run_local_server(
        host='127.0.0.1', port=0, open_browser=True, timeout_seconds=300,
        access_type='offline', prompt='consent',
        authorization_prompt_message='Daca browserul nu s-a deschis, deschide local: {url}',
        success_message='Autorizare primita. Revino in fereastra AutoEditor pentru confirmarea canalului.')


def channel_info(access_token):
    request = urllib.request.Request(
        'https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true',
        headers={'Authorization': 'Bearer ' + access_token})
    with urllib.request.urlopen(request, timeout=30) as response:
        items = json.load(response).get('items', [])
    if len(items) != 1 or not items[0].get('id') or not items[0].get('snippet', {}).get('title'):
        raise SetupError('Nu s-a identificat un singur canal. Autorizeaza contul canalului YouTube dorit.')
    return items[0]['id'], items[0]['snippet']['title']


def store_secrets(repo, configuration, refresh_token, enable_upload=False):
    if not isinstance(refresh_token, str) or not refresh_token.strip():
        raise SetupError('Google nu a returnat refresh_token. Revoca autorizarea veche si reautorizeaza.')
    client = configuration['installed']
    # Disable first. Partial updates must never enable a mismatched credential set.
    gh_call(['variable', 'set', 'YT_UPLOAD_ENABLED', '--repo', repo, '--body', 'false'])
    for name, value in (('YT_CLIENT_ID', client['client_id']),
                        ('YT_CLIENT_SECRET', client['client_secret']),
                        ('YT_REFRESH_TOKEN', refresh_token)):
        # Secret bytes go through stdin, not argv, shell history or a local .env.
        gh_call(['secret', 'set', name, '--repo', repo], secret_input=value)
    if enable_upload:
        gh_call(['variable', 'set', 'YT_UPLOAD_ENABLED', '--repo', repo, '--body', 'true'])


def main(argv=None):
    parser = argparse.ArgumentParser(description='Autorizeaza local YouTube si salveaza direct in GitHub Secrets.')
    parser.add_argument('command', choices=['auth'])
    parser.add_argument('--client-secret', default='client_secret.json')
    parser.add_argument('--repo', default='iZentric/AutoEditor')
    parser.add_argument('--enable-upload', action='store_true', help='activeaza upload-ul privat dupa salvarea tuturor secretelor')
    args = parser.parse_args(argv)
    try:
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            raise SetupError('Ruleaza acest script pe PC-ul tau, nu in GitHub Actions sau sandbox.')
        configuration = load_client(args.client_secret)
        check_github(args.repo)
        print('Se deschide Google. Alege contul/canalul corect si aproba accesul.')
        credentials = authorize(configuration)
        if not credentials.refresh_token:
            raise SetupError('Nu s-a emis refresh_token. Revoca autorizarea veche si reincearca.')
        channel_id, title = channel_info(credentials.token)
        print(f'Canal autorizat: {title} ({channel_id})')
        if input('Scrie DA daca acesta este canalul tau pentru AutoEditor: ').strip().upper() != 'DA':
            print('Oprit. Nu s-a modificat nimic in GitHub.')
            return 1
        store_secrets(args.repo, configuration, credentials.refresh_token, args.enable_upload)
        print('GATA: cele trei setari OAuth au fost salvate in GitHub Secrets. Tokenul nu a fost afisat sau scris local.')
        print('Upload privat activat.' if args.enable_upload else 'Upload-ul ramane oprit; YT_UPLOAD_ENABLED=false.')
        print('Acest pas NU acorda integrarii Arena permisiunea GitHub Workflows.')
        return 0
    except SetupError as error:
        print('OPRIT: ' + str(error), file=sys.stderr)
    except (KeyboardInterrupt, EOFError):
        print('Configurare anulata. Nu partaja coduri sau tokenuri in chat.', file=sys.stderr)
    except Exception as error:
        print(f'Configurare nereusita ({type(error).__name__}). Detaliile sunt ascunse pentru protectia credentialelor. '
              'Verifica autorizarea, YouTube Data API v3 si conexiunea la internet.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
