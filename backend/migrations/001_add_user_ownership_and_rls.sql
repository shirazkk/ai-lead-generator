-- 001_add_user_ownership_and_rls.sql
-- Description: Adds user_id column to leads and outreach tables and enables Row Level Security (RLS).

-- 1. Add user_id column to tables
ALTER TABLE leads ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id) DEFAULT auth.uid();
ALTER TABLE outreach ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id) DEFAULT auth.uid();

-- 2. Enable Row Level Security (RLS)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach ENABLE ROW LEVEL SECURITY;

-- 3. Create Policies for 'leads' table
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can view their own leads') THEN
        CREATE POLICY "Users can view their own leads" 
        ON leads FOR SELECT 
        TO authenticated 
        USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can create their own leads') THEN
        CREATE POLICY "Users can create their own leads" 
        ON leads FOR INSERT 
        TO authenticated 
        WITH CHECK (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can update their own leads') THEN
        CREATE POLICY "Users can update their own leads" 
        ON leads FOR UPDATE 
        TO authenticated 
        USING (auth.uid() = user_id)
        WITH CHECK (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can delete their own leads') THEN
        CREATE POLICY "Users can delete their own leads" 
        ON leads FOR DELETE 
        TO authenticated 
        USING (auth.uid() = user_id);
    END IF;
END $$;

-- 4. Create Policies for 'outreach' table
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can view their own outreach') THEN
        CREATE POLICY "Users can view their own outreach" 
        ON outreach FOR SELECT 
        TO authenticated 
        USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can create their own outreach') THEN
        CREATE POLICY "Users can create their own outreach" 
        ON outreach FOR INSERT 
        TO authenticated 
        WITH CHECK (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can update their own outreach') THEN
        CREATE POLICY "Users can update their own outreach" 
        ON outreach FOR UPDATE 
        TO authenticated 
        USING (auth.uid() = user_id)
        WITH CHECK (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Users can delete their own outreach') THEN
        CREATE POLICY "Users can delete their own outreach" 
        ON outreach FOR DELETE 
        TO authenticated 
        USING (auth.uid() = user_id);
    END IF;
END $$;
