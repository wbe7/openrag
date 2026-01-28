#!/bin/bash
# Fix OpenSearch Index - Delete and Recreate
# This script fixes the jvector engine bug by recreating the index

set -e  # Exit on error

OPENSEARCH_URL="https://opensearch006-coordinating.07e3070e-372b-4a46-8e07-920afef3b9f2.svc.cluster.local:9200"
OPENSEARCH_AUTH="admin:VGggdm5JttgdGc1FYLaOLv1o"
INDEX_NAME="documents"
DIMENSION=1536  # Change this if using a different embedding model

echo "=========================================="
echo "OpenSearch Index Fix Script"
echo "=========================================="
echo ""

# Step 1: Delete the existing index
echo "Step 1: Deleting existing index '$INDEX_NAME'..."
DELETE_RESPONSE=$(curl -sk -u "$OPENSEARCH_AUTH" \
  -X DELETE \
  -w "\n%{http_code}" \
  "$OPENSEARCH_URL/$INDEX_NAME" 2>&1)

HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -n1)
BODY=$(echo "$DELETE_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
  echo "✓ Index deleted successfully (HTTP $HTTP_CODE)"
else
  echo "✗ Failed to delete index (HTTP $HTTP_CODE)"
  echo "Response: $BODY"
  exit 1
fi
echo ""

# Step 2: Wait a moment for deletion to complete
echo "Waiting 2 seconds for index deletion to complete..."
sleep 2
echo ""

# Step 3: Recreate the index with proper mapping
echo "Step 2: Creating index '$INDEX_NAME' with jVector k-NN mapping..."
CREATE_RESPONSE=$(curl -sk -u "$OPENSEARCH_AUTH" \
  -X PUT \
  -H 'Content-Type: application/json' \
  -w "\n%{http_code}" \
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
      \"chunk_embedding\": {
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
}" 2>&1)

HTTP_CODE=$(echo "$CREATE_RESPONSE" | tail -n1)
BODY=$(echo "$CREATE_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ Index created successfully (HTTP $HTTP_CODE)"
else
  echo "✗ Failed to create index (HTTP $HTTP_CODE)"
  echo "Response: $BODY"
  exit 1
fi
echo ""

# Step 4: Verify the index was created
echo "Step 3: Verifying index mapping..."
VERIFY_RESPONSE=$(curl -sk -u "$OPENSEARCH_AUTH" \
  -X GET \
  "$OPENSEARCH_URL/$INDEX_NAME/_mapping?pretty" 2>&1)

if echo "$VERIFY_RESPONSE" | grep -q "knn_vector"; then
  echo "✓ Index mapping verified - knn_vector field found"
else
  echo "⚠ Warning: Could not verify knn_vector field in mapping"
  echo "Response: $VERIFY_RESPONSE"
fi
echo ""

echo "=========================================="
echo "✓ Index fix completed successfully!"
echo "=========================================="
echo ""
echo "You can now ingest documents. The index will automatically"
echo "create additional embedding fields as needed."
echo ""
echo "Example: Bulk indexing documents using curl:"
echo "--------------------------------------------"
echo "curl -vsk \\"
echo "  -u \"\$OPENSEARCH_AUTH\" \\"
echo "  -X POST \\"
echo "  -H \"Content-Type: application/x-ndjson\" \\"
echo "  \"\$OPENSEARCH_URL/_bulk\" \\"
echo "  --data-binary @- <<'EOF'"
echo "{\"index\":{\"_index\":\"$INDEX_NAME\",\"_id\":\"doc-1\"}}"
echo "{\"chunk_embedding_text_embedding_3_small\":[0.123,0.456,...],\"text\":\"Document content\",\"embedding_model\":\"text-embedding-3-small\",\"embedding_dimensions\":$DIMENSION,\"filename\":\"example.pdf\"}"
echo "EOF"
echo ""
