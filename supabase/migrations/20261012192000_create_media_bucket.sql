INSERT INTO storage.buckets (id, name, public)
VALUES ('pioneer-media', 'pioneer-media', false)
ON CONFLICT (id) DO NOTHING;
