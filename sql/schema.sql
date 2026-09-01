CREATE TABLE IF NOT EXISTS sources (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    file TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS documents (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id UUID NOT NULL,
    source_id INTEGER REFERENCES sources(id),
    parent_id INTEGER REFERENCES documents(id),
    content TEXT NOT NULL,
    search_vector TSVECTOR
        GENERATED ALWAYS AS (
            to_tsvector('english', content)
        ) STORED
);

CREATE POLICY tenant_isolation
ON documents
USING (
    tenant_id = current_setting('app.current_tenant', true)::uuid
);

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;


CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id UUID NOT NULL,
    document_id INTEGER REFERENCES documents(id),
    embedding VECTOR(768) NOT NULL
);

CREATE POLICY tenant_isolation
ON embeddings
USING (
    tenant_id = current_setting('app.current_tenant', true)::uuid
);

ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings FORCE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS embeddings_hnsw_idx
ON embeddings
USING hnsw (embedding vector_cosine_ops);


CREATE INDEX IF NOT EXISTS documents_search_vector_gin_idx
ON documents
USING gin (search_vector);


