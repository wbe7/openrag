#!/usr/bin/env python3
"""
Generate OpenAPI specification from Starlette application routes.

This script:
1. Creates the Starlette app (without starting it)
2. Filters routes to only /v1/ endpoints
3. Generates OpenAPI spec from route paths and methods with detailed schemas
4. Writes to docs/openapi/openapi.json
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Set environment variable to skip Langflow connection attempts for faster generation
os.environ["SKIP_LANGFLOW_INIT"] = "1"

# Add src to path so we can import main
# Script is in docs/openapi/, so go up 2 levels to get to repo root
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def get_endpoint_schema(path, method):
    """Get detailed schema for a specific endpoint based on path and method."""
    
    # Chat endpoints
    if path == "/v1/chat" and method == "POST":
        return {
            "summary": "Send a chat message",
            "description": "Send a chat message via Langflow. Supports both streaming and non-streaming responses.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["message"],
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "The chat message"
                                },
                                "chat_id": {
                                    "type": "string",
                                    "description": "Optional chat ID to continue a conversation"
                                },
                                "stream": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "Whether to stream the response"
                                },
                                "filters": {
                                    "type": "object",
                                    "description": "Optional search filters"
                                },
                                "limit": {
                                    "type": "integer",
                                    "default": 10,
                                    "description": "Maximum number of search results"
                                },
                                "score_threshold": {
                                    "type": "number",
                                    "default": 0,
                                    "description": "Minimum relevance score"
                                },
                                "filter_id": {
                                    "type": "string",
                                    "description": "Optional knowledge filter ID"
                                }
                            }
                        },
                        "example": {
                            "message": "What is RAG?",
                            "stream": False
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Chat response (non-streaming) or streaming response (when stream=true)",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "response": {"type": "string"},
                                    "chat_id": {"type": "string"},
                                    "sources": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    }
                                }
                            },
                            "example": {
                                "response": "RAG stands for Retrieval-Augmented Generation...",
                                "chat_id": "abc123",
                                "sources": []
                            }
                        },
                        "text/event-stream": {
                            "schema": {
                                "type": "string",
                                "description": "Server-Sent Events stream"
                            }
                        }
                    }
                },
                "400": {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"}
                                }
                            },
                            "example": {"error": "Message is required"}
                        }
                    }
                },
                "401": {
                    "description": "Unauthorized - Invalid or missing API key",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"}
                                }
                            },
                            "example": {"error": "Invalid API key"}
                        }
                    }
                }
            }
        }
    
    elif path == "/v1/chat" and method == "GET":
        return {
            "summary": "List conversations",
            "description": "List all conversations for the authenticated user.",
            "responses": {
                "200": {
                    "description": "List of conversations",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "conversations": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "chat_id": {"type": "string"},
                                                "title": {"type": "string"},
                                                "created_at": {"type": "string"},
                                                "last_activity": {"type": "string"},
                                                "message_count": {"type": "integer"}
                                            }
                                        }
                                    }
                                }
                            },
                            "example": {
                                "conversations": [{
                                    "chat_id": "abc123",
                                    "title": "What is RAG?",
                                    "created_at": "2024-01-01T00:00:00Z",
                                    "last_activity": "2024-01-01T00:00:00Z",
                                    "message_count": 5
                                }]
                            }
                        }
                    }
                },
                "401": {
                    "description": "Unauthorized - Invalid or missing API key",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    elif path.startswith("/v1/chat/") and method == "GET":
        return {
            "summary": "Get conversation",
            "description": "Get a specific conversation with full message history.",
            "responses": {
                "200": {
                    "description": "Conversation details",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "chat_id": {"type": "string"},
                                    "title": {"type": "string"},
                                    "created_at": {"type": "string"},
                                    "last_activity": {"type": "string"},
                                    "messages": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "role": {"type": "string", "enum": ["user", "assistant"]},
                                                "content": {"type": "string"},
                                                "timestamp": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "404": {
                    "description": "Conversation not found",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"}
                                }
                            },
                            "example": {"error": "Conversation not found"}
                        }
                    }
                }
            }
        }
    
    elif path.startswith("/v1/chat/") and method == "DELETE":
        return {
            "summary": "Delete conversation",
            "description": "Delete a conversation.",
            "responses": {
                "200": {
                    "description": "Conversation deleted successfully",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "success": {"type": "boolean"}
                                }
                            },
                            "example": {"success": True}
                        }
                    }
                }
            }
        }
    
    # Search endpoint
    elif path == "/v1/search" and method == "POST":
        return {
            "summary": "Semantic search",
            "description": "Perform semantic search on documents.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["query"],
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                },
                                "filters": {
                                    "type": "object",
                                    "properties": {
                                        "data_sources": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "document_types": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    },
                                    "description": "Optional search filters"
                                },
                                "limit": {
                                    "type": "integer",
                                    "default": 10,
                                    "description": "Maximum number of results"
                                },
                                "score_threshold": {
                                    "type": "number",
                                    "default": 0,
                                    "description": "Minimum relevance score"
                                }
                            }
                        },
                        "example": {
                            "query": "What is RAG?",
                            "limit": 10,
                            "score_threshold": 0.5
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Search results",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "results": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "filename": {"type": "string"},
                                                "text": {"type": "string"},
                                                "score": {"type": "number"},
                                                "page": {"type": "integer"},
                                                "mimetype": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            },
                            "example": {
                                "results": [{
                                    "filename": "doc.pdf",
                                    "text": "RAG stands for...",
                                    "score": 0.85,
                                    "page": 1,
                                    "mimetype": "application/pdf"
                                }]
                            }
                        }
                    }
                },
                "400": {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"}
                                }
                            },
                            "example": {"error": "Query is required"}
                        }
                    }
                }
            }
        }
    
    # Documents endpoints
    elif path == "/v1/documents/ingest" and method == "POST":
        return {
            "summary": "Ingest document",
            "description": "Ingest a document into the knowledge base. Supports both async (via Langflow) and sync processing.",
            "requestBody": {
                "required": True,
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "required": ["file"],
                            "properties": {
                                "file": {
                                    "type": "string",
                                    "format": "binary",
                                    "description": "Document file to ingest"
                                }
                            }
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Document ingestion initiated",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "task_id": {
                                        "type": "string",
                                        "description": "Task ID for async processing"
                                    },
                                    "status": {
                                        "type": "string",
                                        "enum": ["processing"]
                                    },
                                    "filename": {"type": "string"},
                                    "success": {
                                        "type": "boolean",
                                        "description": "Success flag for sync processing"
                                    },
                                    "document_id": {
                                        "type": "string",
                                        "description": "Document ID for sync processing"
                                    },
                                    "chunks": {
                                        "type": "integer",
                                        "description": "Number of chunks created"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    elif path.startswith("/v1/tasks/") and method == "GET":
        return {
            "summary": "Get task status",
            "description": "Get the status of an ingestion task.",
            "responses": {
                "200": {
                    "description": "Task status",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "task_id": {"type": "string"},
                                    "status": {
                                        "type": "string",
                                        "enum": ["pending", "processing", "completed", "failed"]
                                    },
                                    "total_files": {"type": "integer"},
                                    "processed_files": {"type": "integer"},
                                    "successful_files": {"type": "integer"},
                                    "failed_files": {"type": "integer"},
                                    "files": {"type": "object"}
                                }
                            }
                        }
                    }
                },
                "404": {
                    "description": "Task not found",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"}
                                }
                            },
                            "example": {"error": "Task not found"}
                        }
                    }
                }
            }
        }
    
    elif path == "/v1/documents" and method == "DELETE":
        return {
            "summary": "Delete document",
            "description": "Delete a document from the knowledge base.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["filename"],
                            "properties": {
                                "filename": {
                                    "type": "string",
                                    "description": "Filename of the document to delete"
                                }
                            }
                        },
                        "example": {
                            "filename": "doc.pdf"
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Document deleted successfully",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "success": {"type": "boolean"},
                                    "deleted_chunks": {"type": "integer"}
                                }
                            },
                            "example": {
                                "success": True,
                                "deleted_chunks": 5
                            }
                        }
                    }
                }
            }
        }
    
    # Settings endpoints
    elif path == "/v1/settings" and method == "GET":
        return {
            "summary": "Get settings",
            "description": "Get current OpenRAG configuration (read-only). Sensitive information is never exposed.",
            "responses": {
                "200": {
                    "description": "Current settings",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "agent": {
                                        "type": "object",
                                        "properties": {
                                            "llm_provider": {"type": "string"},
                                            "llm_model": {"type": "string"}
                                        }
                                    },
                                    "knowledge": {
                                        "type": "object",
                                        "properties": {
                                            "embedding_provider": {"type": "string"},
                                            "embedding_model": {"type": "string"},
                                            "chunk_size": {"type": "integer"},
                                            "chunk_overlap": {"type": "integer"}
                                        }
                                    }
                                }
                            },
                            "example": {
                                "agent": {
                                    "llm_provider": "openai",
                                    "llm_model": "gpt-4"
                                },
                                "knowledge": {
                                    "embedding_provider": "openai",
                                    "embedding_model": "text-embedding-3-small",
                                    "chunk_size": 1000,
                                    "chunk_overlap": 200
                                }
                            }
                        }
                    }
                }
            }
        }
    
    elif path == "/v1/settings" and method == "POST":
        return {
            "summary": "Update settings",
            "description": "Update OpenRAG configuration settings. Only a limited subset of settings can be updated.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "chunk_size": {
                                    "type": "integer",
                                    "description": "Chunk size for document processing"
                                },
                                "chunk_overlap": {
                                    "type": "integer",
                                    "description": "Chunk overlap for document processing"
                                }
                            }
                        },
                        "example": {
                            "chunk_size": 1000,
                            "chunk_overlap": 200
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Settings updated successfully",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"}
                                }
                            },
                            "example": {
                                "message": "Configuration updated successfully"
                            }
                        }
                    }
                }
            }
        }
    
    # Knowledge filters endpoints
    elif path == "/v1/knowledge-filters" and method == "POST":
        return {
            "summary": "Create knowledge filter",
            "description": "Create a new knowledge filter.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["name", "queryData"],
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the knowledge filter"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Description of the knowledge filter"
                                },
                                "queryData": {
                                    "type": "object",
                                    "description": "Query data for the filter"
                                },
                                "allowedUsers": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of allowed user IDs"
                                },
                                "allowedGroups": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of allowed group IDs"
                                }
                            }
                        }
                    }
                }
            },
            "responses": {
                "201": {
                    "description": "Knowledge filter created",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "success": {"type": "boolean"},
                                    "filter": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    elif path == "/v1/knowledge-filters/search" and method == "POST":
        return {
            "summary": "Search knowledge filters",
            "description": "Search for knowledge filters by name, description, or query content.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                },
                                "limit": {
                                    "type": "integer",
                                    "default": 20,
                                    "description": "Maximum number of results"
                                }
                            }
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "List of matching knowledge filters",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "success": {"type": "boolean"},
                                    "filters": {
                                        "type": "array",
                                        "items": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    elif path.startswith("/v1/knowledge-filters/") and method == "GET":
        return {
            "summary": "Get knowledge filter",
            "description": "Get a specific knowledge filter by ID.",
            "responses": {
                "200": {
                    "description": "Knowledge filter details",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "success": {"type": "boolean"},
                                    "filter": {"type": "object"}
                                }
                            }
                        }
                    }
                },
                "404": {
                    "description": "Knowledge filter not found",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    elif path.startswith("/v1/knowledge-filters/") and method == "PUT":
        return {
            "summary": "Update knowledge filter",
            "description": "Update a knowledge filter.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "queryData": {"type": "object"}
                            }
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Knowledge filter updated",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "success": {"type": "boolean"},
                                    "filter": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    elif path.startswith("/v1/knowledge-filters/") and method == "DELETE":
        return {
            "summary": "Delete knowledge filter",
            "description": "Delete a knowledge filter.",
            "responses": {
                "200": {
                    "description": "Knowledge filter deleted",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "success": {"type": "boolean"}
                                }
                            },
                            "example": {"success": True}
                        }
                    }
                }
            }
        }
    
    # Default fallback for unknown endpoints
    return None


async def generate_openapi_spec():
    """Generate OpenAPI spec from Starlette app routes."""
    # Import here to avoid issues with async initialization
    from main import create_app

    # Create the app (this initializes services)
    app = await create_app()

    # Filter routes to only /v1/ endpoints
    v1_routes = [route for route in app.routes if route.path.startswith("/v1/")]

    if not v1_routes:
        print("Warning: No /v1/ routes found!")
        return

    print(f"Found {len(v1_routes)} /v1/ routes")

    # Base OpenAPI info
    base_schema = {
        "openapi": "3.0.3",
        "info": {
            "title": "OpenRAG API v1",
            "description": "OpenRAG Public API v1 provides a clean, versioned interface for external integrations.\nAll endpoints require API key authentication via the `X-API-Key` header.",
            "version": "1.0.0",
            "contact": {
                "name": "OpenRAG Support",
                "url": "https://github.com/langflow-ai/openrag",
            },
        },
        "servers": [
            {"url": "http://localhost:8000", "description": "Local development server"},
            {"url": "https://api.openr.ag", "description": "Production server"},
        ],
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for authentication",
                }
            }
        },
        "security": [{"ApiKeyAuth": []}],
        "paths": {},
    }

    # Generate paths from routes
    paths = {}
    for route in v1_routes:
        path = route.path
        methods = [m for m in route.methods if m != "HEAD"]  # Exclude HEAD
        
        if path not in paths:
            paths[path] = {}
        
        for method in methods:
            method_lower = method.lower()
            
            # Get detailed schema for this endpoint
            endpoint_schema = get_endpoint_schema(path, method)
            
            if endpoint_schema:
                # Use the detailed schema
                operation = {
                    "operationId": f"{method_lower}{path.replace('/', '_').replace('{', '').replace('}', '')}",
                    **endpoint_schema
                }
            else:
                # Fallback to basic schema
                operation = {
                    "summary": f"{method} {path}",
                    "operationId": f"{method_lower}{path.replace('/', '_').replace('{', '').replace('}', '')}",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "error": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Unauthorized - Invalid or missing API key",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "error": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                    }
                }
                
                # Add request body for POST/PUT methods
                if method in ["POST", "PUT"]:
                    operation["requestBody"] = {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
            
            # Add path parameters if any
            if "{" in path:
                import re
                param_names = re.findall(r'\{(\w+)\}', path)
                if "parameters" not in operation:
                    operation["parameters"] = []
                operation["parameters"].extend([
                    {
                        "name": param,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": f"The {param.replace('_', ' ')}"
                    }
                    for param in param_names
                ])
            
            paths[path][method_lower] = operation
            print(f"  + {method} {path}")

    base_schema["paths"] = paths

    # Write to file (same directory as script)
    output_path = Path(__file__).parent / "openapi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(base_schema, f, indent=2)

    path_count = len(paths)
    print(f"\nGenerated OpenAPI spec with {path_count} paths")
    print(f"   Written to: {output_path}")
    print(f"\nTip: You can enhance this spec by adding detailed descriptions,")
    print(f"   request/response schemas, and examples to the endpoint docstrings.")


if __name__ == "__main__":
    asyncio.run(generate_openapi_spec())
