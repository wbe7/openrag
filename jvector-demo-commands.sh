#!/bin/bash
# jVector k-NN Demo Script for OpenRAG OpenSearch Deployment

OPENSEARCH_URL="https://opensearch006-coordinating.07e3070e-372b-4a46-8e07-920afef3b9f2.svc.cluster.local:9200"
OPENSEARCH_AUTH="admin:VGggdm5JttgdGc1FYLaOLv1o"
INDEX_NAME="documents"
VECTOR_FIELD="chunk_embedding"
DIMENSION=1536  # Adjust based on your embedding model

echo "############## jVector k-NN Demo for OpenRAG ##############"
echo ""

# 1. Create an index with knn_vector mapping
echo "Step 1: Creating index with jVector k-NN mapping..."
curl -sk -u "$OPENSEARCH_AUTH" \
  -X PUT \
  -H 'Content-Type: application/json' \
  "$OPENSEARCH_URL/$INDEX_NAME?pretty" \
  -d "{
  \"settings\": {
    \"index\": {
      \"knn\": true
    },
    \"number_of_shards\": 1,
    \"number_of_replicas\": 1
  },
  \"mappings\": {
    \"properties\": {
      \"document_id\": {\"type\": \"keyword\"},
      \"filename\": {\"type\": \"keyword\"},
      \"mimetype\": {\"type\": \"keyword\"},
      \"page\": {\"type\": \"integer\"},
      \"text\": {\"type\": \"text\"},
      \"$VECTOR_FIELD\": {
        \"type\": \"knn_vector\",
        \"method\": {
          \"name\": \"disk_ann\",
          \"space_type\": \"l2\",
          \"engine\": \"jvector\",
          \"parameters\": {
            \"m\": 16,
            \"ef_construction\": 100
          }
        },
        \"dimension\": $DIMENSION
      },
      \"embedding_model\": {\"type\": \"keyword\"},
      \"embedding_dimensions\": {\"type\": \"integer\"},
      \"source_url\": {\"type\": \"keyword\"},
      \"connector_type\": {\"type\": \"keyword\"},
      \"owner\": {\"type\": \"keyword\"},
      \"allowed_users\": {\"type\": \"keyword\"},
      \"allowed_groups\": {\"type\": \"keyword\"},
      \"user_permissions\": {\"type\": \"object\"},
      \"group_permissions\": {\"type\": \"object\"},
      \"created_time\": {\"type\": \"date\"},
      \"modified_time\": {\"type\": \"date\"},
      \"indexed_time\": {\"type\": \"date\"},
      \"metadata\": {\"type\": \"object\"}
    }
  }
}"
echo ""
echo ""

# 2. Index sample documents with vectors (example with 4-dimensional vectors for demo)
echo "Step 2: Indexing sample documents with vectors..."
echo "Note: Using 4D vectors for demo. Replace with actual $DIMENSION-dimensional vectors in production."

# Document 1
curl -sk -u "$OPENSEARCH_AUTH" \
  -X PUT \
  -H 'Content-Type: application/json' \
  "$OPENSEARCH_URL/$INDEX_NAME/_doc/doc1?pretty" \
  -d '{
  "document_id": "doc1",
  "filename": "sample1.pdf",
  "text": "Sample document 1",
  "chunk_embedding": [0.1, 0.2, 0.3, 0.4],
  "embedding_model": "test-model",
  "embedding_dimensions": 4
}'

# Document 2
curl -sk -u "$OPENSEARCH_AUTH" \
  -X PUT \
  -H 'Content-Type: application/json' \
  "$OPENSEARCH_URL/$INDEX_NAME/_doc/doc2?pretty" \
  -d '{
  "document_id": "doc2",
  "filename": "sample2.pdf",
  "text": "Sample document 2",
  "chunk_embedding": [0.5, 0.6, 0.7, 0.8],
  "embedding_model": "test-model",
  "embedding_dimensions": 4
}'

# Document 3
curl -sk -u "$OPENSEARCH_AUTH" \
  -X PUT \
  -H 'Content-Type: application/json' \
  "$OPENSEARCH_URL/$INDEX_NAME/_doc/doc3?pretty" \
  -d '{
  "document_id": "doc3",
  "filename": "sample3.pdf",
  "text": "Sample document 3",
  "chunk_embedding": [0.9, 1.0, 1.1, 1.2],
  "embedding_model": "test-model",
  "embedding_dimensions": 4
}'
echo ""
echo ""

# 3. Search for the nearest neighbor of a vector
echo "Step 3: Searching for nearest neighbors..."
curl -sk -u "$OPENSEARCH_AUTH" \
  -X GET \
  -H 'Content-Type: application/json' \
  "$OPENSEARCH_URL/$INDEX_NAME/_search?pretty" \
  -d "{
  \"size\": 3,
  \"query\": {
    \"knn\": {
      \"$VECTOR_FIELD\": {
        \"vector\": [0.1, 0.2, 0.3, 0.4],
        \"k\": 3
      }
    }
  }
}"
echo ""
echo ""

# 4. Search with advanced parameters such as overquery_factor, threshold, rerank_floor
echo "Step 4: Searching with advanced parameters..."
curl -sk -u "$OPENSEARCH_AUTH" \
  -X GET \
  -H 'Content-Type: application/json' \
  "$OPENSEARCH_URL/$INDEX_NAME/_search?pretty" \
  -d "{
  \"size\": 3,
  \"query\": {
    \"knn\": {
      \"$VECTOR_FIELD\": {
        \"vector\": [0.1, 0.2, 0.3, 0.4],
        \"k\": 3,
        \"method_parameters\": {
          \"overquery_factor\": 10,
          \"advanced.threshold\": 0.0,
          \"advanced.rerank_floor\": 0.0
        }
      }
    }
  }
}"
echo ""
echo ""

# 5. Get JVector stats after query
echo "Step 5: Getting jVector stats..."
curl -sk -u "$OPENSEARCH_AUTH" \
  -X GET \
  -H 'Content-Type: application/json' \
  "$OPENSEARCH_URL/_plugins/_knn/stats?pretty&stat=knn_query_visited_nodes,knn_query_expanded_nodes,knn_query_expanded_base_layer_nodes"
echo ""
echo ""

echo "Demo complete!"
