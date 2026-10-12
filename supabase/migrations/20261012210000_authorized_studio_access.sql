BEGIN;
CREATE TABLE public.studio_members (
    user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.studio_members ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.studio_members FROM anon, authenticated;
GRANT SELECT ON public.studio_members TO authenticated;
GRANT ALL ON public.studio_members TO service_role;
CREATE POLICY member_reads_own_membership ON public.studio_members
    FOR SELECT TO authenticated USING (user_id = (SELECT auth.uid()));

GRANT SELECT, INSERT, UPDATE ON public.pioneers, public.pioneer_media TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.pioneers_id_seq TO authenticated;
CREATE POLICY studio_pioneers_read ON public.pioneers FOR SELECT TO authenticated
    USING (EXISTS (SELECT 1 FROM public.studio_members WHERE user_id = (SELECT auth.uid())));
CREATE POLICY studio_pioneers_insert ON public.pioneers FOR INSERT TO authenticated
    WITH CHECK (EXISTS (SELECT 1 FROM public.studio_members WHERE user_id = (SELECT auth.uid())));
CREATE POLICY studio_pioneers_update ON public.pioneers FOR UPDATE TO authenticated
    USING (EXISTS (SELECT 1 FROM public.studio_members WHERE user_id = (SELECT auth.uid())))
    WITH CHECK (EXISTS (SELECT 1 FROM public.studio_members WHERE user_id = (SELECT auth.uid())));
CREATE POLICY studio_media_read ON public.pioneer_media FOR SELECT TO authenticated
    USING (EXISTS (SELECT 1 FROM public.studio_members WHERE user_id = (SELECT auth.uid())));
CREATE POLICY studio_media_insert ON public.pioneer_media FOR INSERT TO authenticated
    WITH CHECK (bucket_id = 'pioneer-media' AND EXISTS (SELECT 1 FROM public.studio_members WHERE user_id = (SELECT auth.uid())));
CREATE POLICY studio_media_update ON public.pioneer_media FOR UPDATE TO authenticated
    USING (bucket_id = 'pioneer-media' AND EXISTS (SELECT 1 FROM public.studio_members WHERE user_id = (SELECT auth.uid())))
    WITH CHECK (bucket_id = 'pioneer-media' AND EXISTS (SELECT 1 FROM public.studio_members WHERE user_id = (SELECT auth.uid())));
CREATE POLICY studio_objects_read ON storage.objects FOR SELECT TO authenticated
    USING (bucket_id = 'pioneer-media' AND EXISTS (SELECT 1 FROM public.studio_members WHERE user_id = (SELECT auth.uid())));
CREATE POLICY studio_objects_insert ON storage.objects FOR INSERT TO authenticated
    WITH CHECK (bucket_id = 'pioneer-media' AND EXISTS (SELECT 1 FROM public.studio_members WHERE user_id = (SELECT auth.uid())));
CREATE POLICY studio_objects_update ON storage.objects FOR UPDATE TO authenticated
    USING (bucket_id = 'pioneer-media' AND EXISTS (SELECT 1 FROM public.studio_members WHERE user_id = (SELECT auth.uid())))
    WITH CHECK (bucket_id = 'pioneer-media' AND EXISTS (SELECT 1 FROM public.studio_members WHERE user_id = (SELECT auth.uid())));
COMMIT;
