"""Telemetry message IDs for OpenRAG backend.

All message IDs start with ORBTA (OpenRAG Backend Telemetry Analytics).
"""


class MessageId:
    """Telemetry message IDs."""
    
    # Category: APPLICATION_STARTUP ------------------------------------------->
    
    # Message: Application started successfully
    ORBTA0001I = "ORBTA0001I"
    # Message: Application startup initiated
    ORBTA0002I = "ORBTA0002I"
    # Message: Application shutdown initiated
    ORBTA0003I = "ORBTA0003I"
    
    # Category: SERVICE_INITIALIZATION ----------------------------------------->
    
    # Message: Services initialized successfully
    ORBTA0010I = "ORBTA0010I"
    # Message: Service initialization started
    ORBTA0011I = "ORBTA0011I"
    # Message: Failed to initialize services
    ORBTA0012E = "ORBTA0012E"
    # Message: Failed to initialize OpenSearch client
    ORBTA0013E = "ORBTA0013E"
    # Message: Failed to generate JWT keys
    ORBTA0014E = "ORBTA0014E"
    
    # Category: OPENSEARCH_SETUP ---------------------------------------------->
    
    # Message: OpenSearch connection established
    ORBTA0020I = "ORBTA0020I"
    # Message: OpenSearch connection failed
    ORBTA0021E = "ORBTA0021E"
    # Message: Waiting for OpenSearch to be ready
    ORBTA0022W = "ORBTA0022W"
    # Message: OpenSearch ready check timeout
    ORBTA0023E = "ORBTA0023E"
    
    # Category: OPENSEARCH_INDEX ---------------------------------------------->
    
    # Message: OpenSearch index created successfully
    ORBTA0030I = "ORBTA0030I"
    # Message: OpenSearch index already exists
    ORBTA0031I = "ORBTA0031I"
    # Message: Failed to create OpenSearch index
    ORBTA0032E = "ORBTA0032E"
    # Message: Failed to initialize index
    ORBTA0033E = "ORBTA0033E"
    # Message: Knowledge filters index created
    ORBTA0034I = "ORBTA0034I"
    # Message: Failed to create knowledge filters index
    ORBTA0035E = "ORBTA0035E"
    
    # Category: DOCUMENT_INGESTION -------------------------------------------->
    
    # Message: Document ingestion started
    ORBTA0040I = "ORBTA0040I"
    # Message: Document ingestion completed successfully
    ORBTA0041I = "ORBTA0041I"
    # Message: Document ingestion failed
    ORBTA0042E = "ORBTA0042E"
    # Message: Default documents ingestion started
    ORBTA0043I = "ORBTA0043I"
    # Message: Default documents ingestion completed
    ORBTA0044I = "ORBTA0044I"
    # Message: Default documents ingestion failed
    ORBTA0045E = "ORBTA0045E"
    
    # Category: DOCUMENT_PROCESSING -------------------------------------------->
    
    # Message: Document processing started
    ORBTA0050I = "ORBTA0050I"
    # Message: Document processing completed
    ORBTA0051I = "ORBTA0051I"
    # Message: Document processing failed
    ORBTA0052E = "ORBTA0052E"
    # Message: Process pool recreation attempted
    ORBTA0053W = "ORBTA0053W"
    
    # Category: AUTHENTICATION ------------------------------------------------>
    
    # Message: Authentication successful
    ORBTA0060I = "ORBTA0060I"
    # Message: Authentication failed
    ORBTA0061E = "ORBTA0061E"
    # Message: User logged out
    ORBTA0062I = "ORBTA0062I"
    # Message: OAuth callback received
    ORBTA0063I = "ORBTA0063I"
    # Message: OAuth callback failed
    ORBTA0064E = "ORBTA0064E"
    
    # Category: CONNECTOR_OPERATIONS ------------------------------------------->
    
    # Message: Connector connection established
    ORBTA0070I = "ORBTA0070I"
    # Message: Connector connection failed
    ORBTA0071E = "ORBTA0071E"
    # Message: Connector sync started
    ORBTA0072I = "ORBTA0072I"
    # Message: Connector sync completed
    ORBTA0073I = "ORBTA0073I"
    # Message: Connector sync failed
    ORBTA0074E = "ORBTA0074E"
    # Message: Connector webhook received
    ORBTA0075I = "ORBTA0075I"
    # Message: Connector webhook failed
    ORBTA0076E = "ORBTA0076E"
    # Message: Failed to load persisted connections
    ORBTA0077W = "ORBTA0077W"
    
    # Category: FLOW_OPERATIONS ------------------------------------------------>
    
    # Message: Flow backup completed
    ORBTA0080I = "ORBTA0080I"
    # Message: Flow backup failed
    ORBTA0081E = "ORBTA0081E"
    # Message: Flow reset detected
    ORBTA0082W = "ORBTA0082W"
    # Message: Flow reset check failed
    ORBTA0083E = "ORBTA0083E"
    # Message: Settings reapplied after flow reset
    ORBTA0084I = "ORBTA0084I"
    
    # Category: TASK_OPERATIONS ------------------------------------------------>
    
    # Message: Task created successfully
    ORBTA0090I = "ORBTA0090I"
    # Message: Task failed
    ORBTA0091E = "ORBTA0091E"
    # Message: Task cancelled
    ORBTA0092I = "ORBTA0092I"
    
    # Category: CHAT_OPERATIONS ------------------------------------------------>
    
    # Message: Chat request received
    ORBTA0100I = "ORBTA0100I"
    # Message: Chat request completed
    ORBTA0101I = "ORBTA0101I"
    # Message: Chat request failed
    ORBTA0102E = "ORBTA0102E"
    
    # Category: ERROR_CONDITIONS ----------------------------------------------->
    
    # Message: Critical error occurred
    ORBTA0110E = "ORBTA0110E"
    # Message: Warning condition
    ORBTA0111W = "ORBTA0111W"
    
    # Category: SETTINGS_OPERATIONS -------------------------------------------->
    
    # Message: Settings updated successfully
    ORBTA0120I = "ORBTA0120I"
    # Message: Settings update failed
    ORBTA0121E = "ORBTA0121E"
    # Message: LLM provider changed
    ORBTA0122I = "ORBTA0122I"
    # Message: LLM model changed
    ORBTA0123I = "ORBTA0123I"
    # Message: Embedding provider changed
    ORBTA0124I = "ORBTA0124I"
    # Message: Embedding model changed
    ORBTA0125I = "ORBTA0125I"
    # Message: System prompt updated
    ORBTA0126I = "ORBTA0126I"
    # Message: Chunk settings updated
    ORBTA0127I = "ORBTA0127I"
    # Message: Docling settings updated
    ORBTA0128I = "ORBTA0128I"
    # Message: Provider credentials updated
    ORBTA0129I = "ORBTA0129I"
    
    # Category: ONBOARDING ----------------------------------------------------->
    
    # Message: Onboarding started
    ORBTA0130I = "ORBTA0130I"
    # Message: Onboarding completed successfully
    ORBTA0131I = "ORBTA0131I"
    # Message: Onboarding failed
    ORBTA0132E = "ORBTA0132E"
    # Message: LLM provider selected during onboarding
    ORBTA0133I = "ORBTA0133I"
    # Message: LLM model selected during onboarding
    ORBTA0134I = "ORBTA0134I"
    # Message: Embedding provider selected during onboarding
    ORBTA0135I = "ORBTA0135I"
    # Message: Embedding model selected during onboarding
    ORBTA0136I = "ORBTA0136I"
    # Message: Sample data ingestion requested
    ORBTA0137I = "ORBTA0137I"
    # Message: Configuration marked as edited
    ORBTA0138I = "ORBTA0138I"

