CREATE TABLE IF NOT EXISTS public.tech_kb (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    kb_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    platform TEXT,
    technologies TEXT[],
    complexity INTEGER,
    criticality TEXT,
    created_date DATE,
    tags TEXT[],
    related_kb TEXT[],
    file_path TEXT,
    quick_summary TEXT,
    quick_fix TEXT,
    diagnostic_time TEXT,
    fix_time TEXT,
    content TEXT, -- Полный текст Markdown
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Индексы для поиска
CREATE INDEX IF NOT EXISTS idx_tech_kb_kb_id ON public.tech_kb(kb_id);
CREATE INDEX IF NOT EXISTS idx_tech_kb_tags ON public.tech_kb USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_tech_kb_technologies ON public.tech_kb USING GIN(technologies);
