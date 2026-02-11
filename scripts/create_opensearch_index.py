#!/usr/bin/env python3
"""
Create an OpenSearch index with the correct mappings for OpenRAG index types.

Usage:
    uv run python scripts/create_opensearch_index.py --index <name>
    make create-os-index INDEX=<name>

Supported index names: documents, knowledge_filters, api_keys
"""
import argparse
import asyncio
import os
import sys

# Add src directory to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from opensearchpy import AsyncOpenSearch
from opensearchpy._async.http_aiohttp import AIOHttpConnection

from config.settings import (
    API_KEYS_INDEX_BODY,
    INDEX_BODY,
    OPENSEARCH_HOST,
    OPENSEARCH_PASSWORD,
    OPENSEARCH_PORT,
    OPENSEARCH_USERNAME,
)

# Knowledge filters index body (matches src/main.py)
KNOWLEDGE_FILTERS_INDEX_BODY = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "name": {"type": "text", "analyzer": "standard"},
            "description": {"type": "text", "analyzer": "standard"},
            "query_data": {"type": "text"},
            "owner": {"type": "keyword"},
            "allowed_users": {"type": "keyword"},
            "allowed_groups": {"type": "keyword"},
            "subscriptions": {"type": "object"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
        }
    }
}

INDEX_BODIES = {
    "documents": INDEX_BODY,
    "knowledge_filters": KNOWLEDGE_FILTERS_INDEX_BODY,
    "api_keys": API_KEYS_INDEX_BODY,
}


async def create_index(index_name: str) -> int:
    if index_name not in INDEX_BODIES:
        print(f"Unsupported index name: {index_name}", file=sys.stderr)
        print("Supported: documents, knowledge_filters, api_keys", file=sys.stderr)
        return 1

    if not OPENSEARCH_PASSWORD:
        print("OPENSEARCH_PASSWORD is not set", file=sys.stderr)
        return 1

    client = AsyncOpenSearch(
        hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
        connection_class=AIOHttpConnection,
        scheme="https",
        use_ssl=True,
        verify_certs=False,
        ssl_assert_fingerprint=None,
        http_auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),
        http_compress=True,
    )

    try:
        exists = await client.indices.exists(index=index_name)
        if exists:
            print(f"Index '{index_name}' already exists, skipping.")
            return 0

        body = INDEX_BODIES[index_name]
        await client.indices.create(index=index_name, body=body)
        print(f"Created OpenSearch index '{index_name}'.")
        return 0
    except Exception as e:
        print(f"Failed to create index '{index_name}': {e}", file=sys.stderr)
        return 1
    finally:
        await client.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an OpenSearch index for OpenRAG")
    parser.add_argument(
        "--index",
        required=True,
        choices=list(INDEX_BODIES),
        help="Index name to create (documents, knowledge_filters, api_keys)",
    )
    args = parser.parse_args()
    return asyncio.run(create_index(args.index))


if __name__ == "__main__":
    sys.exit(main())
