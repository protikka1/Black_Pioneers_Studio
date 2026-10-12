from pathlib import Path
from unittest.mock import Mock, patch
import sqlite3

import pytest

from black_pioneers_studio.cloud import Backend
from scripts.import_supabase import read_local, plan_import, import_plan


def test_api_keys_and_user_tokens_have_distinct_headers():
    response = Mock(ok=True, status_code=200, content=b'{}')
    response.json.return_value = {}
    with patch('black_pioneers_studio.cloud.requests.request', return_value=response) as request:
        backend = Backend('https://example.supabase.co', 'sb_secret_test')
        backend.request('GET', '/rest/v1/pioneers')
        assert request.call_args.kwargs['headers'] == {'apikey': 'sb_secret_test'}
        backend.token = 'user.jwt.token'
        backend.request('GET', '/rest/v1/pioneers')
        assert request.call_args.kwargs['headers']['Authorization'] == 'Bearer user.jwt.token'


def test_error_does_not_expose_secret_or_response_body():
    response = Mock(ok=False, status_code=401, text='private secret-key password')
    with patch('black_pioneers_studio.cloud.requests.request', return_value=response):
        with pytest.raises(RuntimeError) as result:
            Backend('https://example.supabase.co', 'secret-key').request('GET', '/test')
    assert 'secret-key' not in str(result.value)
    assert '401' in str(result.value)


def test_login_denies_unlisted_account():
    backend = Backend('https://example.supabase.co', 'sb_publishable_test')
    with patch.object(backend, 'request', return_value={'access_token': 'jwt', 'refresh_token': 'refresh'}), patch.object(backend, 'rows', return_value=[]):
        with pytest.raises(RuntimeError, match='not authorized'):
            backend.login('person@example.com', 'private-password')


def test_refresh_rotates_expiring_session():
    backend = Backend('https://example.supabase.co', 'public')
    backend.refresh_token = 'old'
    backend.expires_at = 0
    with patch.object(backend, 'request', return_value={'access_token': 'new.jwt', 'refresh_token': 'new', 'expires_in': 3600}) as request:
        backend.refresh_if_needed()
        backend.refresh_if_needed()
    assert request.call_count == 1
    assert backend.token == 'new.jwt'


def test_pagination_does_not_drop_records():
    backend = Backend('https://example.supabase.co', 'public')
    with patch.object(backend, 'request', side_effect=[[{'id': i} for i in range(500)], [{'id': 500}]]) as request:
        assert len(backend.rows('pioneers')) == 501
        assert request.call_args.kwargs['params']['offset'] == '500'


def test_media_upload_reuses_existing_content(tmp_path):
    file = tmp_path / 'portrait.jpg'
    file.write_bytes(b'fake-image')
    backend = Backend('https://example.supabase.co', 'public')
    with patch.object(backend, 'rows', return_value=[{'id': 'existing'}]), patch.object(backend, 'request') as request:
        assert backend.upload(5, file, 'images')['id'] == 'existing'
        request.assert_not_called()


def test_import_reads_without_modifying_sqlite(tmp_path):
    db = tmp_path / 'pioneers.db'
    with sqlite3.connect(db) as connection:
        connection.execute('CREATE TABLE pioneers (id INTEGER, name TEXT, project_title TEXT)')
        connection.execute("INSERT INTO pioneers VALUES (1, 'MLK', 'Black Pioneers: First in American History')")
    before = db.read_bytes()
    assert read_local(db)[0]['name'] == 'MLK'
    assert db.read_bytes() == before


def test_conflicts_stop_before_import(tmp_path):
    row = {'id': 1, 'name': 'MLK', 'biography': 'local'}
    with pytest.raises(ValueError, match='differs'):
        plan_import([row], [{'name': 'MLK', 'biography': 'remote'}], tmp_path)


def test_missing_media_folder_is_reported(tmp_path):
    with pytest.raises(ValueError, match='Cannot find media folder'):
        plan_import([{'id': 1, 'name': 'MLK', 'folder_path': ''}], [], tmp_path)


def test_import_remaps_ids_without_mutating_source(tmp_path):
    file = tmp_path / 'image.jpg'
    file.write_bytes(b'fake')
    row = {'id': 1, 'name': 'MLK', 'biography': 'bio'}
    backend = Mock()
    backend.create_pioneer.return_value = 42
    backend.upload.return_value = {'object_path': 'pioneers/42/images/image.jpg'}
    backend.media.return_value = [{'object_path': 'pioneers/42/images/image.jpg'}]
    import_plan(backend, [(row, None, [(file, 'images')])])
    assert backend.upload.call_args.args[0] == 42
    assert row['id'] == 1
    assert 'id' not in backend.create_pioneer.call_args.kwargs
    assert file.read_bytes() == b'fake'


def test_shared_app_requires_login_before_reading_collection(tmp_path):
    import os
    import subprocess
    import sys
    code = '''
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from black_pioneers_studio.cloud import Backend
with patch.object(Backend, 'pioneers', return_value=[]) as records, patch.object(Backend, 'media', return_value=[]), patch.object(Backend, 'login'):
    app = AppTest.from_file('app.py').run(timeout=30)
    assert not app.exception, app.exception
    assert app.title[0].value == 'Sign in to Black Pioneers Studio'
    records.assert_not_called()
    app.text_input[0].set_value('owner@example.com')
    app.text_input[1].set_value('test-password')
    app.button[0].click().run(timeout=30)
    assert not app.exception, app.exception
    assert records.called
    for page in ['Create Pioneer', 'Create Short', 'Video Library', 'Tools', 'Settings', 'Dashboard']:
        app.sidebar.radio[0].set_value(page).run(timeout=30)
        assert not app.exception, (page, app.exception)
'''
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, SUPABASE_ENABLED='true', SUPABASE_URL='https://example.supabase.co',
               SUPABASE_PUBLISHABLE_KEY='sb_publishable_test', BLACK_PIONEERS_DATA_DIR=str(tmp_path))
    result = subprocess.run([sys.executable, '-c', code], cwd=root, env=env,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr


def test_google_login_exchanges_nonce_and_keeps_membership_gate():
    backend = Backend('https://example.supabase.co', 'sb_publishable_test')
    with patch.object(backend, 'request', return_value={'access_token': 'supabase.jwt', 'refresh_token': 'refresh'}) as request, patch.object(backend, 'rows', return_value=[{'user_id': 'owner'}]):
        backend.login_google('google.id.token', 'raw-nonce')
        assert request.call_args.kwargs['params'] == {'grant_type': 'id_token'}
        assert request.call_args.kwargs['body'] == {'provider': 'google', 'id_token': 'google.id.token', 'nonce': 'raw-nonce'}
    assert backend.token == 'supabase.jwt'
    other = Backend('https://example.supabase.co', 'sb_publishable_test')
    with patch.object(other, 'request', return_value={'access_token': 'supabase.jwt', 'refresh_token': 'refresh'}), patch.object(other, 'rows', return_value=[]):
        with pytest.raises(RuntimeError, match='not authorized'):
            other.login_google('google.id.token', 'raw-nonce')


def test_google_component_contains_no_raw_nonce_or_secrets(tmp_path):
    import os
    import subprocess
    import sys
    code = '''
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from black_pioneers_studio.cloud import Backend
import hashlib
with patch('streamlit.components.v1.declare_component') as declare, patch.object(Backend, 'pioneers', return_value=[]):
    declare.return_value.return_value = None
    app = AppTest.from_file('app.py').run(timeout=30)
    assert not app.exception, app.exception
    args = declare.return_value.call_args.kwargs
    assert 'nonce' not in args
    assert 'secret' not in args
    assert args['hashed_nonce'] == hashlib.sha256(app.session_state['google_nonce'].encode()).hexdigest()
'''
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, SUPABASE_ENABLED='true', SUPABASE_URL='https://example.supabase.co',
               SUPABASE_PUBLISHABLE_KEY='sb_publishable_test', GOOGLE_CLIENT_ID='test.apps.googleusercontent.com',
               BLACK_PIONEERS_DATA_DIR=str(tmp_path))
    result = subprocess.run([sys.executable, '-c', code], cwd=root, env=env,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
