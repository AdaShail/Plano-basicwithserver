-- Database schema for Pattern Learning System
-- This schema supports storing event patterns, outcomes, and similarity matching

-- Table for storing event patterns from successful events
CREATE TABLE IF NOT EXISTS event_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(255) NOT NULL UNIQUE,
    user_id UUID REFERENCES auth.users(id),
    
    -- Event context data (JSON for flexibility)
    event_context JSONB NOT NULL,
    
    -- Timeline data
    timeline_data JSONB NOT NULL,
    
    -- Budget allocation data
    budget_allocation JSONB NOT NULL,
    
    -- Feedback data
    feedback_data JSONB NOT NULL,
    
    -- Calculated metrics
    success_score DECIMAL(3,2) NOT NULL CHECK (success_score >= 0 AND success_score <= 10),
    complexity_score DECIMAL(3,2) DEFAULT 0,
    
    -- Usage statistics
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing extracted success patterns
CREATE TABLE IF NOT EXISTS success_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(100) NOT NULL, -- 'timeline', 'budget', 'activity_sequence', etc.
    
    -- Pattern conditions and recommendations (JSON for flexibility)
    event_types TEXT[] NOT NULL,
    conditions JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    
    -- Pattern metrics
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    supporting_event_count INTEGER DEFAULT 1,
    
    -- Supporting events (array of event IDs)
    supporting_events TEXT[] NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing feedback analyses
CREATE TABLE IF NOT EXISTS feedback_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    budget_tier VARCHAR(20),
    
    -- Analysis results
    analysis_data JSONB NOT NULL,
    
    -- Metadata
    feedback_count INTEGER NOT NULL,
    reliability_score VARCHAR(10) NOT NULL, -- 'high', 'medium', 'low'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint for event_type + budget_tier combination
    UNIQUE(event_type, budget_tier)
);

-- Table for storing recommendation adjustments
CREATE TABLE IF NOT EXISTS recommendation_adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    adjustment_type VARCHAR(50) NOT NULL, -- 'timeline', 'budget', 'activity', 'vendor'
    target_category VARCHAR(100) NOT NULL,
    
    -- Adjustment details
    adjustment_factor DECIMAL(5,3) NOT NULL,
    confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    reasoning TEXT NOT NULL,
    supporting_feedback_count INTEGER NOT NULL,
    
    -- Associated event type
    event_type VARCHAR(50) NOT NULL,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_event_patterns_event_id ON event_patterns(event_id);
CREATE INDEX IF NOT EXISTS idx_event_patterns_user_id ON event_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_event_patterns_success_score ON event_patterns(success_score);
CREATE INDEX IF NOT EXISTS idx_event_patterns_created_at ON event_patterns(created_at);

-- GIN indexes for JSONB columns to support efficient querying
CREATE INDEX IF NOT EXISTS idx_event_patterns_context ON event_patterns USING GIN(event_context);
CREATE INDEX IF NOT EXISTS idx_event_patterns_timeline ON event_patterns USING GIN(timeline_data);
CREATE INDEX IF NOT EXISTS idx_event_patterns_budget ON event_patterns USING GIN(budget_allocation);

CREATE INDEX IF NOT EXISTS idx_success_patterns_type ON success_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_success_patterns_confidence ON success_patterns(confidence_score);
CREATE INDEX IF NOT EXISTS idx_success_patterns_conditions ON success_patterns USING GIN(conditions);

CREATE INDEX IF NOT EXISTS idx_feedback_analyses_event_type ON feedback_analyses(event_type);
CREATE INDEX IF NOT EXISTS idx_feedback_analyses_budget_tier ON feedback_analyses(budget_tier);

CREATE INDEX IF NOT EXISTS idx_recommendation_adjustments_type ON recommendation_adjustments(adjustment_type);
CREATE INDEX IF NOT EXISTS idx_recommendation_adjustments_event_type ON recommendation_adjustments(event_type);
CREATE INDEX IF NOT EXISTS idx_recommendation_adjustments_active ON recommendation_adjustments(is_active);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update updated_at
CREATE TRIGGER update_event_patterns_updated_at BEFORE UPDATE ON event_patterns 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_success_patterns_updated_at BEFORE UPDATE ON success_patterns 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feedback_analyses_updated_at BEFORE UPDATE ON feedback_analyses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recommendation_adjustments_updated_at BEFORE UPDATE ON recommendation_adjustments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE event_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE success_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendation_adjustments ENABLE ROW LEVEL SECURITY;

-- Policy for event_patterns: users can only access their own patterns
CREATE POLICY "Users can view their own event patterns" ON event_patterns
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own event patterns" ON event_patterns
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own event patterns" ON event_patterns
    FOR UPDATE USING (auth.uid() = user_id);

-- Policies for success_patterns: readable by all authenticated users, writable by service role
CREATE POLICY "Authenticated users can view success patterns" ON success_patterns
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Service role can manage success patterns" ON success_patterns
    FOR ALL USING (auth.role() = 'service_role');

-- Policies for feedback_analyses: readable by all authenticated users, writable by service role
CREATE POLICY "Authenticated users can view feedback analyses" ON feedback_analyses
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Service role can manage feedback analyses" ON feedback_analyses
    FOR ALL USING (auth.role() = 'service_role');

-- Policies for recommendation_adjustments: readable by all authenticated users, writable by service role
CREATE POLICY "Authenticated users can view recommendation adjustments" ON recommendation_adjustments
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Service role can manage recommendation adjustments" ON recommendation_adjustments
    FOR ALL USING (auth.role() = 'service_role');