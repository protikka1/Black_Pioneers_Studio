# Supabase migrations

See [the root README](../README.md#shared-supabase-database-and-media-import-and-connect)
for the complete CLI, import, authentication, and shared backend setup.

- `20261012183000`: matching pioneer table and media index.
- `20261012192000`: private Storage bucket. This also records the migration
  already created on the user's Mac; do not duplicate it under another timestamp.
- `20261012210000`: authorized studio members and row-level access policies.

The importer reads SQLite without modifying it and assigns cloud IDs deliberately.
The CLI manages migration history separately from SQLite's schema_migrations.
Existing absolute folder paths are never shared-media references.

All members share one collection. Anonymous visitors and non-member accounts are
excluded. The running app uses a publishable key plus a user's authenticated token;
the privileged import key is prompted only in the local import process.
