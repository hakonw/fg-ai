-- Run this in your Supabase SQL Editor

-- 1. Table for Metadata & Queue
create table images (
  id uuid default gen_random_uuid() primary key,
  download_url text unique not null,
  preview_url text,
  motive text,
  place text,
  date text,
  status text default 'pending', -- pending, processing, indexed, failed
  created_at timestamp with time zone default now()
);

-- 2. Indexes for speed
create index idx_images_status on images(status);
create index idx_images_download on images(download_url);
