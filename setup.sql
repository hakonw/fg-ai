-- 1. Tables for Metadata & Queue
create table motives (
  id uuid default gen_random_uuid() primary key,
  fg_motive_id uuid unique,
  title text,
  date date,
  place text,
  security_level text,
  created_at timestamp with time zone default now()
);

create table images (
  id uuid default gen_random_uuid() primary key,
  fg_photo_id uuid,
  motive_id uuid references motives(id),
  security_level text,
  download_url text unique,
  preview_url text,
  image_width int,
  image_height int,
  status text default 'pending', -- pending, processing, indexed, failed
  created_at timestamp with time zone default now()
);

-- 2. Indexes for speed
create index idx_images_status on images(status);
create index idx_images_download on images(download_url);
create unique index idx_images_fg_photo_id on images(fg_photo_id);
create index idx_images_motive_id on images(motive_id);

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
    order by created_at desc
    limit limit_count
    for update skip locked
  )
  returning *;
$$;
