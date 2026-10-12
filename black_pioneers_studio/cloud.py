"""Supabase REST adapter. User tokens stay scoped to a Streamlit session."""
from __future__ import annotations

import hashlib
import base64
import json
import mimetypes
import os
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

from .paths import PROJECT_TITLE

BUCKET = 'pioneer-media'


def settings() -> dict:
    import streamlit as st
    try:
        values = dict(st.secrets)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        values = {}
    for name in ('SUPABASE_ENABLED', 'SUPABASE_URL', 'SUPABASE_PUBLISHABLE_KEY'):
        if name in os.environ:
            values[name] = os.environ[name]
    return values


def enabled() -> bool:
    return str(settings().get('SUPABASE_ENABLED', False)).lower() in ('true', '1', 'yes')


def current_backend():
    if not enabled():
        return None
    import streamlit as st
    backend = st.session_state.get('supabase_backend')
    if backend is None:
        raise RuntimeError('Sign in before using the shared collection.')
    backend.refresh_if_needed()
    return backend


class Backend:
    def __init__(self, url: str, key: str, token: str | None = None):
        self.url = url.rstrip('/')
        if not self.url.startswith('https://'):
            raise ValueError('Use your hosted Supabase HTTPS project URL.')
        self.key = key
        self.token = token or key
        self.refresh_token = None
        self.expires_at = float('inf')
        self.refresh_lock = threading.RLock()

    def request(self, method, path, *, params=None, body=None, data=None, headers=None):
        auth = {'apikey': self.key}
        if not self.token.startswith(('sb_publishable_', 'sb_secret_')):
            auth['Authorization'] = f'Bearer {self.token}'
        auth.update(headers or {})
        try:
            response = requests.request(method, self.url + path, params=params,
                                        json=body, data=data, headers=auth, timeout=(15, 300))
            if not response.ok:
                # Never print response bodies, request headers, URLs, tokens or passwords.
                raise RuntimeError(f'Supabase request failed (HTTP {response.status_code}). Check access and project settings.')
            if response.status_code == 204 or not response.content:
                return None
            return response.json()
        except requests.RequestException:
            raise RuntimeError('Could not reach Supabase. Check your internet connection.') from None

    def _set_session(self, session):
        self.token = session['access_token']
        self.refresh_token = session['refresh_token']
        self.expires_at = time.time() + session.get('expires_in', 3600)

    def login(self, email, password):
        session = self.request('POST', '/auth/v1/token', params={'grant_type': 'password'},
                               body={'email': email, 'password': password})
        self._set_session(session)
        if not self.rows('studio_members', {'select': 'user_id', 'limit': '1'}):
            raise RuntimeError('This account is not authorized for the studio collection.')

    def refresh_if_needed(self):
        with self.refresh_lock:
            if self.refresh_token and time.time() >= self.expires_at - 120:
                result = self.request('POST', '/auth/v1/token', params={'grant_type': 'refresh_token'},
                                      body={'refresh_token': self.refresh_token})
                self._set_session(result)

    def rows(self, table, filters=None):
        filters = dict(filters or {})
        requested_limit = int(filters.pop('limit')) if 'limit' in filters else None
        result = []
        offset = 0
        while True:
            page = self.request('GET', '/rest/v1/' + table,
                                params={**filters, 'limit': str(min(500, requested_limit)) if requested_limit else '500', 'offset': str(offset)})
            result.extend(page)
            if len(page) < 500 or requested_limit is not None:
                return result
            offset += len(page)

    def pioneers(self):
        return self.rows('pioneers', {'select': '*', 'project_title': 'eq.' + PROJECT_TITLE,
                                     'order': 'created_at.desc,id.desc'})

    def create_pioneer(self, name, category='', achievement='', biography='', **extra):
        timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
        row = {'name': name.strip(), 'category': category, 'achievement': achievement,
               'biography': biography, 'project_title': PROJECT_TITLE, 'folder_path': '',
               'created_at': timestamp, 'updated_at': timestamp, **extra}
        return self.request('POST', '/rest/v1/pioneers', body=row,
                            headers={'Prefer': 'return=representation'})[0]['id']

    def media(self, pioneer_id=None, *, generated=False):
        filters = {'select': '*', 'order': 'created_at.desc,id.desc'}
        if pioneer_id is not None:
            filters['pioneer_id'] = f'eq.{pioneer_id}'
        if generated:
            filters['kind'] = 'eq.video'
            filters['object_path'] = 'like.pioneers/*/output/*'
        return self.rows('pioneer_media', filters)

    def upload(self, pioneer_id, path: Path, category: str):
        mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        kind = 'image' if mime.startswith('image/') else 'video' if mime.startswith('video/') else 'audio'
        if not mime.startswith(('image/', 'video/', 'audio/')):
            raise ValueError('Unsupported media type.')
        digest = hashlib.sha256()
        with path.open('rb') as source:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(block)
        name = digest.hexdigest() + path.suffix.lower()
        object_path = f'pioneers/{int(pioneer_id)}/{category}/{name}'
        existing = self.rows('pioneer_media', {'select': '*', 'bucket_id': 'eq.' + BUCKET,
                                              'object_path': 'eq.' + object_path})
        if existing:
            return existing[0]
        with path.open('rb') as source:
            self.request('POST', '/storage/v1/object/' + BUCKET + '/' + quote(object_path, safe='/'),
                         data=source, headers={'Content-Type': mime, 'x-upsert': 'true'})
        row = {'pioneer_id': int(pioneer_id), 'kind': kind, 'bucket_id': BUCKET,
               'object_path': object_path, 'original_filename': path.name,
               'content_type': mime, 'size_bytes': path.stat().st_size}
        return self.request('POST', '/rest/v1/pioneer_media',
                            params={'on_conflict': 'bucket_id,object_path'}, body=row,
                            headers={'Prefer': 'resolution=merge-duplicates,return=representation'})[0]

    def signed_url(self, media):
        result = self.request('POST', '/storage/v1/object/sign/' + media['bucket_id'] + '/' +
                              quote(media['object_path'], safe='/'), body={'expiresIn': 600})
        path = result.get('signedURL') or result.get('signedUrl')
        if not path:
            raise RuntimeError('Supabase did not return a media URL.')
        return path if path.startswith('https://') else self.url + '/storage/v1' + path

    def download(self, media, destination: Path):
        destination.parent.mkdir(parents=True, exist_ok=True)
        url = self.signed_url(media)
        temporary = destination.with_suffix(destination.suffix + '.part')
        try:
            with requests.get(url, stream=True, timeout=(15, 300)) as response:
                if not response.ok:
                    raise RuntimeError(f'Media download failed (HTTP {response.status_code}).')
                with temporary.open('wb') as output:
                    for block in response.iter_content(1024 * 1024):
                        output.write(block)
            temporary.replace(destination)
        except requests.RequestException:
            raise RuntimeError('Media download failed. Check your internet connection.') from None
        finally:
            temporary.unlink(missing_ok=True)
        return destination


def require_login():
    """Run before querying any collection data. Never use service keys in the app."""
    if not enabled():
        return
    import streamlit as st
    config = settings()
    key = config.get('SUPABASE_PUBLISHABLE_KEY', '')
    forbidden = key.startswith('sb_secret_')
    if key.count('.') == 2:
        try:
            payload = key.split('.')[1]
            forbidden = forbidden or json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4))).get('role') == 'service_role'
        except (ValueError, TypeError):
            forbidden = True
    if forbidden:
        st.error('Use a publishable/anon key in the app, never a secret/service_role key.')
        st.stop()
    if 'supabase_backend'  in st.session_state:
        try:
            current_backend()
        except RuntimeError:
            st.session_state.pop('supabase_backend', None)
            st.error('Your shared session expired. Please sign in again.')
            st.stop()
        if st.sidebar.button('Sign out of shared collection'):
            # Clear session-scoped tokens and any previews/session state.
            st.session_state.clear()
            st.rerun()
        return
    st.title('Sign in to Black Pioneers Studio')
    with st.form('supabase_sign_in', clear_on_submit=True):
        email = st.text_input('Email')
        password = st.text_input('Password', type='password')
        submitted = st.form_submit_button('Sign in')
    if submitted:
        try:
            backend = Backend(config['SUPABASE_URL'], config['SUPABASE_PUBLISHABLE_KEY'])
            backend.login(email.strip(), password)
            st.session_state['supabase_backend'] = backend
            st.rerun()
        except (RuntimeError, ValueError, KeyError) as exc:
            st.error(str(exc) if not isinstance(exc, KeyError) else 'Supabase configuration is incomplete.')
    st.stop()
