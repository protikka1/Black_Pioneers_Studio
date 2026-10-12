"""Read-only local import; defaults to dry-run and never deletes local/remote data."""
from __future__ import annotations

import argparse
import getpass
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from black_pioneers_studio.cloud import Backend, BUCKET
from black_pioneers_studio.paths import PROJECT_TITLE

EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.mp4', '.mov', '.m4v', '.mp3', '.wav', '.m4a', '.ogg'}
FIELDS = ('name', 'category', 'achievement', 'biography', 'created_at', 'updated_at')


def read_local(database: Path):
    if not database.is_file():
        raise ValueError(f'Database does not exist: {database}')
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute('SELECT * FROM pioneers WHERE project_title = ? ORDER BY id', (PROJECT_TITLE,)).fetchall()
    return [dict(row) for row in rows]


def local_files(row, data_dir: Path):
    folder = Path(row['folder_path']).expanduser() if row.get('folder_path') else None
    if folder is not None and not folder.is_absolute():
        folder = data_dir / folder
    if folder is None or not folder.is_dir():
        matches = list((data_dir / 'output' / 'pioneers').glob(f"{row['id']}_*"))
        folder = matches[0] if len(matches) == 1 else None
    if folder is None or not folder.is_dir():
        raise ValueError(f"Cannot find media folder for {row['name']}. Check folder_path before importing.")
    # Import recognized permanent media, never temporary prepared images/captions.
    result = []
    for category in ('images', 'videos', 'audio', 'music', 'output'):
        for path in sorted((folder / category).rglob('*')):
            if path.is_file() and path.suffix.lower() in EXTENSIONS:
                if path.is_symlink() or not path.resolve().is_relative_to(folder.resolve()):
                    raise ValueError('Media links outside the pioneer folder are not imported.')
                result.append((path, category))
    return result


def plan_import(rows, remote, data_dir):
    by_name = {row['name']: row for row in remote}
    plan = []
    for row in rows:
        existing = by_name.get(row['name'])
        if existing:
            for field in ('category', 'achievement', 'biography'):
                if (existing.get(field) or '') != (row.get(field) or ''):
                    raise ValueError(f"Cloud record differs for {row['name']} ({field}); resolve it before importing. No records overwritten.")
        plan.append((row, existing, local_files(row, data_dir)))
    return plan


def import_plan(backend, plan):
    for row, existing, files in plan:
        if existing:
            cloud_id = existing['id']
        else:
            values = {field: row.get(field) or '' for field in FIELDS}
            cloud_id = backend.create_pioneer(**values)
        expected_keys = set()
        for path, category in files:
            item = backend.upload(cloud_id, path, category)
            expected_keys.add(item["object_path"])
        print(f"Imported {row['name']}: {len(files)} files (cloud ID {cloud_id}).")
        # Verify each expected content-key exists before reporting success.
        actual_keys = {item["object_path"] for item in backend.media(cloud_id)}
        if not expected_keys.issubset(actual_keys):
            raise RuntimeError('Media verification count did not match. Rerun the import to resume.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--database', type=Path)
    parser.add_argument('--url', required=True, help='Your hosted Supabase HTTPS project URL.')
    parser.add_argument('--authorize-email', help='Grant an existing Supabase Auth user access to this shared studio, only with --apply.')
    parser.add_argument('--apply', action='store_true', help='Import after creating a SQLite backup; default is read-only planning.')
    args = parser.parse_args()
    data_dir = args.data_dir.expanduser().resolve()
    database = (args.database or data_dir / 'database' / 'pioneers.db').expanduser().resolve()
    rows = read_local(database)
    if not rows:
        raise ValueError('No pioneer records found in this database. Check --data-dir/--database.')
    key = getpass.getpass('Supabase secret/service_role API key (hidden, used only for import): ')
    backend = Backend(args.url, key)
    remote = backend.pioneers()
    bucket = backend.request('GET', '/storage/v1/bucket/' + BUCKET)
    if bucket.get('public'):
        raise ValueError('The media bucket must be private before import.')
    plan = plan_import(rows, remote, data_dir)
    print(f'Plan: {len(plan)} pioneers, {sum(len(files) for _, _, files in plan)} media files.')
    print('Existing matching records are reused; conflicting records stop the import.')
    if not args.apply:
        print('Dry-run complete. No remote data changed. Rerun with --apply to import.')
        return
    backup_dir = data_dir / 'migration-backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f'pioneers_{datetime.now():%Y%m%d_%H%M%S_%f}.db'
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as source:
        with sqlite3.connect(backup) as destination:
            source.backup(destination)
    print(f'SQLite backup saved: {backup}')
    import_plan(backend, plan)
    if args.authorize_email:
        matches = []
        page = 1
        while True:
            result = backend.request('GET', '/auth/v1/admin/users', params={'page': page, 'per_page': 100})
            users = result.get('users', [])
            matches.extend(user for user in users if (user.get('email') or '').lower() == args.authorize_email.lower())
            if len(users) < 100:
                break
            page += 1
        if len(matches) != 1:
            raise ValueError('Create the account in Supabase Authentication first; exactly one matching user is required.')
        backend.request('POST', '/rest/v1/studio_members', body={'user_id': matches[0]['id']},
                        params={'on_conflict': 'user_id'}, headers={'Prefer': 'resolution=ignore-duplicates'})
        print('Existing account authorized for the shared collection.')
    print('Import complete. Local database and media remain unchanged.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, sqlite3.Error) as exc:
        print(f'Import stopped: {exc}', file=sys.stderr)
        sys.exit(1)
