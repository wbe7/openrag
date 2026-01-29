# Enterprise Connectors Plugin Architecture - Brainstorming

## Current State Analysis

The existing connector architecture in OpenRAG uses:

- **Base interface**: `BaseConnector` ABC in [src/connectors/base.py](../src/connectors/base.py)
- **Manual registration**: Factory method in [src/connectors/connection_manager.py](../src/connectors/connection_manager.py)
- **Hardcoded discovery**: Connector types are hardcoded in `get_available_connector_types()`
- **Tight coupling**: Adding a connector requires modifying `connection_manager.py`

```python
# Current factory pattern (connection_manager.py:373-391)
def _create_connector(self, config):
    if config.connector_type == "google_drive":
        return GoogleDriveConnector(config.config)
    elif config.connector_type == "sharepoint":
        return SharePointConnector(config.config)
    # ... hardcoded for each type
```

---

## Approach 1: Python Entry Points Plugin System

**Concept**: Use Python's standard entry points mechanism for connector discovery. Enterprise package registers connectors via `pyproject.toml` entry points.

**Architecture**:

```
openrag (open source)
├── src/connectors/base.py          # BaseConnector interface
├── src/connectors/registry.py      # Plugin discovery via entry_points
└── pyproject.toml                  # Defines entry point group

openrag-enterprise-connectors (private)
├── src/enterprise_connectors/
│   ├── salesforce/connector.py
│   ├── confluence/connector.py
│   └── ...
└── pyproject.toml                  # Registers connectors to entry point
```

**Implementation**:

```python
# openrag/src/connectors/registry.py
from importlib.metadata import entry_points

def discover_connectors() -> Dict[str, Type[BaseConnector]]:
    """Discover all registered connectors via entry points"""
    connectors = {}
    
    # Built-in connectors
    connectors["google_drive"] = GoogleDriveConnector
    connectors["sharepoint"] = SharePointConnector
    
    # Discover plugins
    eps = entry_points(group="openrag.connectors")
    for ep in eps:
        connector_class = ep.load()
        connectors[ep.name] = connector_class
    
    return connectors
```

```toml
# openrag-enterprise-connectors/pyproject.toml
[project.entry-points."openrag.connectors"]
salesforce = "enterprise_connectors.salesforce:SalesforceConnector"
confluence = "enterprise_connectors.confluence:ConfluenceConnector"
servicenow = "enterprise_connectors.servicenow:ServiceNowConnector"
```

**Pros**:

- Standard Python pattern, well-understood
- Clean separation - enterprise package is just another pip install
- Works with any Python package manager (pip, uv, poetry)
- No code changes needed in OpenRAG when adding connectors
- Supports versioning and dependency management

**Cons**:

- Requires enterprise package to be installed in the same environment
- Docker images need to include enterprise package at build time
- Private PyPI or git authentication needed for enterprise package

---

## Approach 2: Environment-based Dynamic Import

**Concept**: Enterprise connectors are specified via environment variable pointing to a module path. OpenRAG dynamically imports at runtime.

**Architecture**:

```
openrag (open source)
└── src/connectors/
    ├── base.py
    └── dynamic_loader.py    # Loads from OPENRAG_CONNECTOR_MODULES

openrag-enterprise-connectors (private)
└── enterprise_connectors/
    └── __init__.py          # Exports connector classes
```

**Implementation**:

```python
# openrag/src/connectors/dynamic_loader.py
import os
import importlib

CONNECTOR_MODULES = os.getenv("OPENRAG_CONNECTOR_MODULES", "").split(",")

def load_enterprise_connectors():
    connectors = {}
    for module_path in CONNECTOR_MODULES:
        if not module_path.strip():
            continue
        module = importlib.import_module(module_path)
        for name, cls in module.CONNECTORS.items():
            connectors[name] = cls
    return connectors
```

```python
# enterprise_connectors/__init__.py
from .salesforce import SalesforceConnector
from .confluence import ConfluenceConnector

CONNECTORS = {
    "salesforce": SalesforceConnector,
    "confluence": ConfluenceConnector,
}
```

**Pros**:

- Simple to implement
- No changes to packaging or build process
- Can dynamically enable/disable connectors
- Works well with Docker volume mounts

**Cons**:

- Less type-safe than entry points
- Requires module to be in Python path
- Error-prone string-based configuration
- No dependency management for connectors

---

## Approach 3: Connector-as-a-Service (Microservice)

**Concept**: Enterprise connectors run as a separate microservice with a standard API. OpenRAG calls this service via HTTP/gRPC.

**Architecture**:

```
┌─────────────────────┐     HTTP/gRPC      ┌────────────────────────────┐
│                     │◄──────────────────►│                            │
│  OpenRAG (OSS)      │                    │  Enterprise Connector      │
│                     │                    │  Service (Private)         │
│  - ConnectorProxy   │                    │                            │
│    implements       │                    │  - Salesforce Connector    │
│    BaseConnector    │                    │  - Confluence Connector    │
│                     │                    │  - ServiceNow Connector    │
└─────────────────────┘                    └────────────────────────────┘
```

**Implementation**:

```python
# openrag/src/connectors/proxy_connector.py
class EnterpriseConnectorProxy(BaseConnector):
    """Proxies connector calls to enterprise service"""
    
    def __init__(self, config):
        self.service_url = os.getenv("ENTERPRISE_CONNECTOR_SERVICE_URL")
        self.connector_type = config.get("connector_type")
    
    async def list_files(self, page_token=None, max_files=None):
        response = await httpx.post(
            f"{self.service_url}/connectors/{self.connector_type}/list",
            json={"page_token": page_token, "max_files": max_files}
        )
        return response.json()
    
    async def get_file_content(self, file_id: str):
        response = await httpx.get(
            f"{self.service_url}/connectors/{self.connector_type}/files/{file_id}"
        )
        return ConnectorDocument(**response.json())
```

```python
# enterprise-connector-service/main.py (FastAPI)
@app.post("/connectors/{connector_type}/list")
async def list_files(connector_type: str, request: ListRequest):
    connector = get_connector(connector_type)
    return await connector.list_files(request.page_token, request.max_files)
```

**Pros**:

- Complete isolation - different repos, different languages possible
- Independent scaling and deployment
- Clear API boundary
- No code coupling between OSS and enterprise
- Can be developed by separate teams
- Easier to license/sell separately

**Cons**:

- Network latency for every operation
- More complex deployment (another service to manage)
- Need to handle service discovery, auth, retries
- Large file transfers over network
- Operational overhead

---

## Approach 4: Docker Build-time Extension (Recommended for Simplicity)

**Concept**: Enterprise Docker images extend the base OpenRAG image, adding enterprise connectors at build time.

**Architecture**:

```
openrag (open source)
├── Dockerfile.backend           # Base image
└── src/connectors/
    └── plugin_loader.py         # Loads from well-known paths

openrag-enterprise (private)
├── Dockerfile                   # FROM langflowai/openrag-backend
├── connectors/
│   ├── salesforce/
│   └── confluence/
└── register_connectors.py       # Registration script
```

**Implementation**:

```dockerfile
# openrag-enterprise/Dockerfile
FROM langflowai/openrag-backend:latest

# Copy enterprise connectors
COPY connectors/ /app/src/connectors/enterprise/

# Copy registration script
COPY register_connectors.py /app/

# Register connectors at build time
RUN python /app/register_connectors.py

# Or: Set environment variable for runtime registration
ENV OPENRAG_ENTERPRISE_CONNECTORS_PATH=/app/src/connectors/enterprise
```

```python
# openrag/src/connectors/plugin_loader.py
import os
import importlib.util
from pathlib import Path

ENTERPRISE_PATH = os.getenv("OPENRAG_ENTERPRISE_CONNECTORS_PATH")

def load_enterprise_connectors():
    if not ENTERPRISE_PATH or not Path(ENTERPRISE_PATH).exists():
        return {}
    
    connectors = {}
    for connector_dir in Path(ENTERPRISE_PATH).iterdir():
        if connector_dir.is_dir() and (connector_dir / "connector.py").exists():
            spec = importlib.util.spec_from_file_location(
                f"enterprise.{connector_dir.name}",
                connector_dir / "connector.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            connectors[connector_dir.name] = module.Connector
    return connectors
```

**Pros**:

- Simple to implement and understand
- Clear separation - private repo builds on top of public image
- No runtime dependencies between repos
- Works with existing Docker infrastructure
- Single image output for deployment

**Cons**:

- Requires rebuilding image when OpenRAG updates
- Enterprise connectors tied to specific OpenRAG versions
- No independent deployment of connector updates

---

## Approach 5: Kubernetes Operator Pattern

**Concept**: A Kubernetes operator manages OpenRAG deployments and can inject enterprise connectors via custom resources.

**Architecture**:

```yaml
# OpenRAG Custom Resource
apiVersion: openrag.io/v1
kind: OpenRAGCluster
metadata:
  name: enterprise-deployment
spec:
  version: "0.2.0"
  connectors:
    enterprise:
      image: ghcr.io/myorg/openrag-enterprise-connectors:v1
      connectors:
        - salesforce
        - confluence
        - servicenow
```

**Implementation**: The operator would:

1. Deploy base OpenRAG pods
2. Mount enterprise connector code as volumes
3. Set environment variables for connector discovery
4. Manage upgrades and rollbacks

**Pros**:

- Native Kubernetes experience
- Declarative configuration
- Automatic version management
- Can manage complex multi-tenant deployments
- Enterprise features as add-on resources

**Cons**:

- Requires Kubernetes
- Significant development effort for operator
- Overkill for simpler deployments
- Learning curve for users

---

## Approach 6: Package Extras with Private PyPI Index

**Concept**: OpenRAG defines optional extras that pull from a private PyPI index.

**Architecture**:

```toml
# openrag/pyproject.toml
[project.optional-dependencies]
enterprise = ["openrag-enterprise-connectors>=1.0"]

# User installs with:
# pip install openrag[enterprise] --extra-index-url https://pypi.mycompany.com
```

**Pros**:

- Standard Python packaging
- Version pinning and dependency resolution
- Clear enterprise vs. community editions

**Cons**:

- Requires private PyPI infrastructure
- Authentication complexity
- Couples OpenRAG releases to enterprise package

---

## Recommendation Matrix

| Approach | Summary | Impl. Effort | Deploy Complexity | Isolation | Cost of Ownership | Best For | Pros | Cons |
|----------|---------|--------------|-------------------|-----------|-------------------|----------|------|------|
| Entry Points | Standard Python plugin via importlib entry points | Medium | Low | Medium | Low | Python shops | Standard pattern, auto-discovery, versioning | Needs same env, private PyPI/git auth |
| Dynamic Import | Load connectors via env var module paths | Low | Low | Low | Very Low | Quick implementation | Simple, no packaging changes, Docker volumes | Not type-safe, error-prone, no dep mgmt |
| Microservice | Separate HTTP/gRPC service for connectors | High | High | High | High | Large enterprises, separate teams | Complete isolation, independent scaling, any language | Network latency, complex ops, file transfer overhead |
| Docker Extension | Enterprise image extends base OpenRAG image | Low | Low | High | Low | Simple deployments | Simple, clear separation, single image | Rebuild on updates, version coupling |
| K8s Operator | K8s operator injects connectors via CRDs | Very High | Medium | High | Medium-High | K8s-native orgs | Declarative, auto-upgrades, multi-tenant | Requires K8s, significant dev effort |
| Package Extras | Optional extras pulling from private PyPI | Medium | Medium | Medium | Medium | PyPI-centric workflows | Standard packaging, version pinning | Needs private PyPI, auth complexity |

### Quick Comparison Rankings

- **Lowest Cost of Ownership**: Dynamic Import > Docker Extension > Entry Points > Package Extras > K8s Operator > Microservice
- **Best Isolation**: Microservice = K8s Operator = Docker Extension > Entry Points = Package Extras > Dynamic Import
- **Fastest to Implement**: Dynamic Import > Docker Extension > Entry Points > Package Extras > Microservice > K8s Operator
- **Most Scalable**: K8s Operator > Microservice > Entry Points > Docker Extension > Package Extras > Dynamic Import

---

## Suggested Hybrid Approach

Combine **Entry Points** (for Python purists) + **Docker Extension** (for production):

1. **Base OpenRAG changes**:
   - Add entry points discovery in `connection_manager.py`
   - Support `OPENRAG_ENTERPRISE_CONNECTORS_PATH` for path-based loading
   - Export `BaseConnector` and data models as public API

2. **Enterprise connector repo**:
   - Implement connectors using `BaseConnector` interface
   - Publish as Python package with entry points
   - Provide Docker image that extends `openrag-backend`

3. **Users choose deployment method**:
   - `pip install openrag-enterprise-connectors` for development
   - Use enterprise Docker image for production
   - Kubernetes users can use either method

---

## Required Changes to OpenRAG

1. **[src/connectors/connection_manager.py](../src/connectors/connection_manager.py)**:
   - Replace hardcoded factory with plugin discovery
   - Support both entry points and path-based loading

2. **[src/connectors/__init__.py](../src/connectors/__init__.py)**:
   - Export `BaseConnector` and models as public API

3. **[pyproject.toml](../pyproject.toml)**:
   - Define `openrag.connectors` entry point group

4. **Documentation**:
   - Connector development guide
   - Enterprise integration guide
