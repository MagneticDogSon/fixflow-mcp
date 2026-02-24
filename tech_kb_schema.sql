-- FixFlow KB Schema (Supabase PostgreSQL 17)
-- Project: hbwrduqbmuupxhtndrta | Region: eu-north-1

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- Main table
CREATE TABLE IF NOT EXISTS public.fixflow_kb (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    kb_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    platform TEXT DEFAULT 'unknown',
    technologies TEXT[] DEFAULT '{}',
    complexity INTEGER DEFAULT 1 CHECK (complexity BETWEEN 1 AND 10),
    criticality TEXT DEFAULT 'low' CHECK (criticality IN ('low', 'medium', 'high', 'critical')),
    tags TEXT[] DEFAULT '{}',
    related_kb TEXT[] DEFAULT '{}',
    content TEXT NOT NULL,
    quick_summary TEXT,
    fix_time TEXT,

    -- Community metrics
    submitted_by TEXT DEFAULT 'anonymous',
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    status TEXT DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived', 'spam')),

    -- Usage tracking
    view_count INTEGER DEFAULT 0,
    applied_count INTEGER DEFAULT 0,
    solved_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Vector search
    embedding extensions.vector(384),

    -- Full-text search
    fts tsvector,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_fixflow_kb_fts ON public.fixflow_kb USING GIN(fts);
CREATE INDEX IF NOT EXISTS idx_fixflow_kb_category ON public.fixflow_kb(category);
CREATE INDEX IF NOT EXISTS idx_fixflow_kb_status ON public.fixflow_kb(status);

-- FTS + updated_at trigger
CREATE OR REPLACE FUNCTION public.handle_fixflow_kb_changes()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    NEW.fts =
        setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.quick_summary, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(array_to_string(NEW.tags, ' '), '')), 'C') ||
        setweight(to_tsvector('english', coalesce(NEW.content, '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER fixflow_kb_changes
    BEFORE INSERT OR UPDATE ON public.fixflow_kb
    FOR EACH ROW EXECUTE FUNCTION handle_fixflow_kb_changes();

-- Search function (FTS + Vector hybrid)
CREATE OR REPLACE FUNCTION public.search_kb_cards(
    query_text TEXT,
    query_embedding extensions.vector(384) DEFAULT NULL,
    match_limit INT DEFAULT 20
)
RETURNS TABLE (
    kb_id TEXT, title TEXT, category TEXT, platform TEXT,
    technologies TEXT[], complexity INT, criticality TEXT,
    tags TEXT[], quick_summary TEXT, fix_time TEXT,
    similarity FLOAT
)
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    IF query_embedding IS NOT NULL THEN
        RETURN QUERY
        SELECT t.kb_id, t.title, t.category, t.platform,
            t.technologies, t.complexity, t.criticality,
            t.tags, t.quick_summary, t.fix_time,
            (1 - (t.embedding <=> query_embedding))::FLOAT
        FROM fixflow_kb t
        WHERE t.status = 'published' AND t.embedding IS NOT NULL
        ORDER BY t.embedding <=> query_embedding
        LIMIT match_limit;
    ELSE
        RETURN QUERY
        SELECT t.kb_id, t.title, t.category, t.platform,
            t.technologies, t.complexity, t.criticality,
            t.tags, t.quick_summary, t.fix_time,
            ts_rank(t.fts, websearch_to_tsquery('english', query_text))::FLOAT
        FROM fixflow_kb t
        WHERE t.status = 'published'
          AND t.fts @@ websearch_to_tsquery('english', query_text)
        ORDER BY 11 DESC
        LIMIT match_limit;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Event tracking function
CREATE OR REPLACE FUNCTION public.track_card_event(
    p_kb_id TEXT,
    p_event TEXT
)
RETURNS JSON
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_success_rate FLOAT;
BEGIN
    IF p_event NOT IN ('view', 'applied', 'solved', 'failed') THEN
        RETURN json_build_object('error', 'Invalid event type');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM fixflow_kb WHERE kb_id = p_kb_id AND status = 'published') THEN
        RETURN json_build_object('error', 'Card not found');
    END IF;

    IF p_event = 'view' THEN
        UPDATE fixflow_kb SET view_count = view_count + 1, last_used_at = now() WHERE kb_id = p_kb_id;
    ELSIF p_event = 'applied' THEN
        UPDATE fixflow_kb SET applied_count = applied_count + 1, last_used_at = now() WHERE kb_id = p_kb_id;
    ELSIF p_event = 'solved' THEN
        UPDATE fixflow_kb SET solved_count = solved_count + 1, upvotes = upvotes + 1, last_used_at = now() WHERE kb_id = p_kb_id;
    ELSIF p_event = 'failed' THEN
        UPDATE fixflow_kb SET failed_count = failed_count + 1, downvotes = downvotes + 1, last_used_at = now() WHERE kb_id = p_kb_id;
    END IF;

    SELECT CASE WHEN (solved_count + failed_count) > 0
        THEN ROUND(solved_count::numeric / (solved_count + failed_count)::numeric * 100, 1)
        ELSE NULL END
    INTO v_success_rate FROM fixflow_kb WHERE kb_id = p_kb_id;

    RETURN json_build_object(
        'kb_id', p_kb_id, 'event', p_event,
        'view_count', (SELECT view_count FROM fixflow_kb WHERE kb_id = p_kb_id),
        'applied_count', (SELECT applied_count FROM fixflow_kb WHERE kb_id = p_kb_id),
        'solved_count', (SELECT solved_count FROM fixflow_kb WHERE kb_id = p_kb_id),
        'failed_count', (SELECT failed_count FROM fixflow_kb WHERE kb_id = p_kb_id),
        'success_rate', v_success_rate
    );
END;
$$ LANGUAGE plpgsql;

-- RLS
ALTER TABLE public.fixflow_kb ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read published cards"
    ON public.fixflow_kb FOR SELECT USING (status = 'published');

CREATE POLICY "Validated insert for anon"
    ON public.fixflow_kb FOR INSERT TO anon
    WITH CHECK (kb_id ~ '^[A-Z]+_[A-Z]+_\d+$' AND length(content) > 200 AND category ~ '^[a-z0-9_-]+$' AND status = 'published');

CREATE POLICY "Validated insert for authenticated"
    ON public.fixflow_kb FOR INSERT TO authenticated
    WITH CHECK (kb_id ~ '^[A-Z]+_[A-Z]+_\d+$' AND length(content) > 200 AND category ~ '^[a-z0-9_-]+$');

CREATE POLICY "Anyone can vote on cards"
    ON public.fixflow_kb FOR UPDATE TO anon, authenticated
    USING (status = 'published') WITH CHECK (status = 'published');
