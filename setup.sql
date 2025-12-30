-- Run this in your Supabase SQL Editor

-- 1. Table for Metadata & Queue
create table images (
  id uuid default gen_random_uuid() primary key,
  download_url text unique not null,
  page_url text,
  preview_url text,
  motive text,
  place text,
  date text,
  image_width int,
  image_height int,
  status text default 'pending', -- pending, processing, indexed, failed
  created_at timestamp with time zone default now()
);

-- 2. Indexes for speed
create index idx_images_status on images(status);
create index idx_images_download on images(download_url);

-- 3. Atomic change
-- Allows a worker to atomically claim N images
create or replace function get_pending_images(limit_count int)
returns setof images
language sql
as $$
  update images
  set status = 'processing'
  where id in (
    select id
    from images
    where status = 'pending'
    limit limit_count
    for update skip locked
  )
  returning *;
$$;
