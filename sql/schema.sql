CREATE TABLE IF NOT EXISTS sources (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    file TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS documents (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    content TEXT NOT NULL,
    search_vector TSVECTOR
        GENERATED ALWAYS AS (
            to_tsvector('english', content)
        ) STORED
);


CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    embedding VECTOR(768) NOT NULL
);


CREATE INDEX IF NOT EXISTS embeddings_hnsw_idx
ON embeddings
USING hnsw (embedding vector_cosine_ops);


CREATE INDEX IF NOT EXISTS documents_search_vector_gin_idx
ON documents
USING gin (search_vector);