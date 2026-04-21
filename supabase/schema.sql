-- Run this in the Supabase SQL Editor before starting the build

-- Enable pgvector
create extension if not exists vector;

-- Main embeddings table
create table if not exists bill_passages (
  id bigserial primary key,
  content text not null,
  embedding vector(1536),
  source text not null,
  chapter text,
  title text,
  date_written text,
  chunk_index int,
  token_count int
);

-- Fast similarity search function
create or replace function search_bill_passages(
  query_embedding vector(1536),
  match_count int default 5,
  match_threshold float default 0.7
)
returns table (
  id bigint,
  content text,
  source text,
  chapter text,
  title text,
  similarity float
)
language sql stable
as $$
  select
    id, content, source, chapter, title,
    1 - (embedding <=> query_embedding) as similarity
  from bill_passages
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by embedding <=> query_embedding
  limit match_count;
$$;

-- Index for fast search (run after ingesting data)
-- create index on bill_passages using ivfflat (embedding vector_cosine_ops)
--   with (lists = 100);
