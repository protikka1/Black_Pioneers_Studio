# Prepare Black Pioneers Studio's shared database

This migration matches the current SQLite `pioneers` columns and unique constraint.
It adds `pioneer_media` to index images, narration audio, and video Storage objects.
It does not change the running app, import data, or copy the source code to Supabase.
SQLite's `schema_migrations` is not application data: the CLI tracks PostgreSQL
migrations separately. Legacy timestamp strings and `folder_path` are retained so
existing records can be imported without silently reinterpreting local timestamps.
Media object paths must replace machine-specific absolute paths in the future adapter.

## CLI on your Mac

Use Node 20 or newer. From your existing project folder:

```bash
cd ~/Projects/black-pioneers-cloud
npx --yes supabase --version
npx supabase login
npx supabase link --project-ref YOUR_PROJECT_REF
npx supabase db push --dry-run
npx supabase db push
```

The project reference is the dashboard URL segment after `/project/`.
Replace `YOUR_PROJECT_REF`; it is not the display name or database password.
Enter credentials only in the CLI's login/password prompts. No manual PATH change
or Docker/local database is needed for this hosted-project push workflow.
The committed `config.toml` already initializes the CLI; do not run init again.
Run this against the newly created, empty Supabase project. If tables already exist,
inspect them first rather than resetting or dropping the remote database.

After the push, check Table Editor for `pioneers` and `pioneer_media`.
In Storage, create a bucket named `pioneer-media`, with Public disabled.
Actual files must be uploaded through the Storage API, not inserted into storage.objects.

## What comes next

1. Back up local SQLite and media before import.
2. Import pioneers; remap or preserve IDs deliberately and advance the identity sequence
   if existing IDs are imported explicitly. Avoid duplicate names in the same project.
3. Upload media into the private bucket and record object keys in `pioneer_media`.
4. Add an authenticated database/Storage adapter and configure both apps with secrets.
5. Verify counts, image retrieval, and video playback before switching the backend.

RLS is enabled and ordinary client access is denied initially. Service credentials
are privileged: keep them in server secrets, never browser code or GitHub. The app
currently has no user login; do not expose privileged writes through a public app.
Both existing localhost and Cloud apps remain on SQLite until the adapter is implemented.
