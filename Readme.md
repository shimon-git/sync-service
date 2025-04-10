<h1>📦 <code>Sync-Service</code></h1>

<p>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" />
  <img src="https://img.shields.io/badge/FastAPI-🚀-green" />
  <img src="https://img.shields.io/badge/status-stable-brightgreen" />
</p>

<h2>📚 Table of Contents</h2>
<ul>
  <li><a href="#description">🔍 Description</a></li>
  <li><a href="#responsibilities">🎯 Responsibilities</a></li>
  <li><a href="#prerequisites">📥 Prerequisites</a></li>
  <li><a href="#tech-stack">⚙️ Tech Stack</a></li>
  <li><a href="#folder-structure">🧱 Folder Structure</a></li>
  <li><a href="#how-to-run">🚀 How to Run</a></li>
  <li><a href="#environment-variables">🔐 Environment Variables</a></li>
  <li>
    <a href="#configuration-file-structure">🛠 Configuration File Structure</a>
  </li>
  <li><a href="#api-endpoints">📡 API Endpoints</a></li>
  <li><a href="#core-classes">🧠 Core Classes</a></li>
  <li>
    <a href="#function-overview-by-class">🔧 Function Overview by Class</a>
  </li>
  <li><a href="#api-documentation">🧪 API Documentation</a></li>
  <li><a href="#notes">📝 Notes</a></li>
  <li><a href="#future-enhancements">🔮 Future Enhancements</a></li>
</ul>

<h2 id="description">🔍 Description</h2>
<p>
  This service handles the synchronization between the application and VMware
  infrastructure. Its main purpose is to ensure the application always stays
  up-to-date with the latest VM state, metadata, and lifecycle changes such as
  orphaning, reactivation, and renaming.
</p>

<hr />

<h2 id="responsibilities">🎯 Responsibilities</h2>
<ul>
  <li>Check and update the database with new VMs</li>
  <li>Compare VMs in the database against those in VMware</li>
  <li>
    Detect changes in VMs such as renames, power state, VMware Tools status, and
    orphaned VMs
  </li>
  <li>Update Redis user sessions with newly orphaned VMs</li>
</ul>

<hr />

<h2 id="prerequisites">📥 Prerequisites</h2>
<ul>
  <li>Python 3.10+</li>
  <li>MongoDB server running and accessible</li>
  <li>Redis server running and accessible</li>
  <li>Access to ESXi infrastructure</li>
</ul>

<h2 id="tech-stack">⚙️ Tech Stack</h2>
<ul>
  <li>Python 3.10+</li>
  <li>FastAPI – Web framework for building the service</li>
  <li>Uvicorn – ASGI server for running FastAPI</li>
  <li>Redis (via <code>redis.asyncio</code>) – Session and caching layer</li>
  <li>HTTPX – Async HTTP client for external API communication</li>
  <li>Pydantic – Data validation and schema generation</li>
  <li>PyVMomi – VMware vSphere API Python bindings</li>
  <li>PyYAML – YAML config parsing</li>
  <li>PyMongo – MongoDB interaction layer</li>
</ul>

<hr />

<h2 id="folder-structure">🧱 Folder Structure</h2>
<pre><code>sync-service/
├── .dockerignore              # Files to exclude from Docker context
├── clean.bat                  # Windows script to clean local build artifacts
├── clean.sh                   # Bash script to clean local build artifacts
├── Dockerfile                 # Docker build configuration
├── main.py                    # Entry point for starting the service
├── mongodb.py                 # MongoDB connector and helper logic
├── Readme.md                  # Documentation for this service
├── redis_client.py            # Redis session manager and utilities
├── requirements.txt           # Python dependencies
├── run.bat                    # Windows script to run the service locally
├── run.sh                     # Bash script to run the service locally
├── server.py                  # FastAPI route and app configuration
├── sync.py                    # Core sync logic between ESXi and DB/Redis
├── sync.yaml                  # Configuration file for sync-service
</code></pre>

<hr />

<h2 id="how-to-run">🚀 How to Run</h2>
<pre><code><strong>Windows</strong>
1. Open Command Prompt
2. Navigate to the project directory:
   cd sync-service
3. Run the service using the provided script:
   run.bat

This script will:

- Create a virtual environment (if not already present)
- Activate the virtual environment
- Install required dependencies from requirements.txt
- Run main.py

<strong>Linux/macOS</strong>

1. Open Terminal
2. Navigate to the project directory:
   cd sync-service
3. Make sure the script is executable:
   chmod +x run.sh
4. Run the service using:
   ./run.sh

This script will:

- Create a virtual environment (if not already present)
- Activate the virtual environment
- Install required dependencies from requirements.txt
- Run main.py
  </code></pre>

<hr />

<h2 id="environment-variables">🔐 Environment Variables</h2>
<table border="1" cellpadding="5">
  <tr>
    <th>Variable Name</th>
    <th>Description</th>
  </tr>
  <tr>
    <td>CONFIG_FILE</td>
    <td>
      Path to the service YAML configuration file (e.g., <code>sync.yaml</code>)
    </td>
  </tr>
</table>

<hr />

<h2 id="configuration-file-structure">🛠 Configuration File Structure</h2>
<p>
  The service uses a YAML configuration file, defined via the
  <code>CONFIG_FILE</code> environment variable. Below is an explanation of the
  available fields:
</p>

<pre><code>esxi_hosts:
  - host: 192.168.198.17       # IP address of the ESXi host
    port: 443                  # HTTPS port for ESXi (default: 443)
    username: <USER>           # ESXi login username
    password: <PASSWORD>       # ESXi login password

mongodb:
  host: localhost              # MongoDB host (can be IP or hostname)
  port: 27017                  # MongoDB port
  username: <USER>             # MongoDB username
  password: <PASSWORD>         # MongoDB password
  db: esxi                     # Name of the MongoDB database
  collection: vms              # Collection where VM documents are stored

api_server:
  host: 0.0.0.0                # IP to bind the API server (0.0.0.0 for all interfaces)
  port: 4000                   # Port to expose the FastAPI service

sync:
  interval: 120                # Sync interval in seconds (how often VMs are re-synced)
  timeout: 30                  # Request timeout duration (in seconds)

endpoints:
  vm-group-service-rename-vm: http://vm-group-service/vms/group/rename-vms  # Endpoint for VM group renaming
  auth-service-rename-vm: http://auth-service/rename/vm                    # Endpoint for session renaming

redis:
  host: localhost              # Redis server hostname
  port: 6379                   # Redis server port
</code></pre>

<hr />

<h2 id="api-endpoints">📡 API Endpoints</h2>
<table border="1" cellpadding="5">
  <tr>
    <th>Method</th>
    <th>Endpoint</th>
    <th>Description</th>
  </tr>
  <tr>
    <td>GET</td>
    <td><code>/sync/status</code></td>
    <td>Returns whether a sync operation is currently in progress.</td>
  </tr>
  <tr>
    <td>GET</td>
    <td><code>/sync/now</code></td>
    <td>Triggers an immediate synchronization of all VMs.</td>
  </tr>
  <tr>
    <td>POST</td>
    <td><code>/sync/vms</code></td>
    <td>Triggers sync for a specific list of VMs (by UUID or name).</td>
  </tr>
</table>
<p>
  <em
    >Note: A full interactive reference is available via Swagger UI (FastAPI
    auto-docs).</em
  >
</p>

<hr />

<h2 id="core-classes">🧠 Core Classes</h2>
<table border="1" cellpadding="5">
  <tr>
    <th>Class Name</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><code>Sync</code></td>
    <td>
      Handles all logic related to synchronizing VMs between ESXi, MongoDB, and
      Redis. Includes renaming, orphaning, reactivation, and sync status
      operations.
    </td>
  </tr>
  <tr>
    <td><code>Mongodb</code></td>
    <td>
      Wrapper class for MongoDB operations. Manages VM data in the database and
      supports create, read, update, and delete operations.
    </td>
  </tr>
  <tr>
    <td><code>RedisClient</code></td>
    <td>
      Manages Redis-based user sessions and handles allowed/orphaned VM states
      inside each session. Includes helper methods for sync impact.
    </td>
  </tr>
  <tr>
    <td><code>APIServer</code></td>
    <td>
      Defines FastAPI endpoints for interacting with sync status and triggering
      sync manually or for specific VMs.
    </td>
  </tr>
</table>

<hr />

<h2 id="function-overview-by-class">🔧 Function Overview by Class</h2>
<h3>📄 <code>main.py</code> - Application Entrypoint</h3>
<table border="1" cellpadding="5">
  <tr>
    <th>Function</th>
    <th>Arguments</th>
    <th>Returns</th>
    <th>Description</th>
  </tr>

  <tr>
    <td><code>load_config</code></td>
    <td>–</td>
    <td>dict</td>
    <td>
      Loads and parses the YAML configuration file defined by the
      <code>CONFIG_FILE</code> environment variable.
    </td>
  </tr>

  <tr>
    <td><code>create_esxi_instances</code></td>
    <td>
      esxi_conf: list, mongodb_instance: Mongodb, redis_conf: dict, endpoints:
      dict
    </td>
    <td>list[Sync]</td>
    <td>
      Creates and returns a list of <code>Sync</code> class instances—one for
      each ESXi host.
    </td>
  </tr>

  <tr>
    <td><code>create_mongodb_instance</code></td>
    <td>mongodb_conf: dict</td>
    <td>Mongodb</td>
    <td>
      Initializes and returns a <code>Mongodb</code> class instance with the
      given configuration.
    </td>
  </tr>

  <tr>
    <td><code>create_api_instance</code></td>
    <td>api_conf: dict, sync_instances: list</td>
    <td>APIServer</td>
    <td>
      Returns an <code>APIServer</code> instance with handlers for checking and
      triggering sync.
    </td>
  </tr>

  <tr>
    <td><code>perform_sync</code></td>
    <td>sync_instances: list</td>
    <td>None</td>
    <td>
      Runs a sync cycle across all sync instances and prints results or errors
      to console.
    </td>
  </tr>

  <tr>
    <td><code>run</code></td>
    <td>sync_instances: list, interval: int, timeout: int</td>
    <td>None</td>
    <td>
      Main background loop that waits for a scheduled interval or manual trigger
      and runs sync in a thread.
    </td>
  </tr>

  <tr>
    <td><code>main</code></td>
    <td>–</td>
    <td>None</td>
    <td>
      Initializes configuration, instances, sync thread, and launches the API
      server.
    </td>
  </tr>
</table>

<h3>📄 <code>RedisClient</code></h3>
<table border="1" cellpadding="5">
  <tr>
    <th>Function</th>
    <th>Arguments</th>
    <th>Returns</th>
    <th>Description</th>
  </tr>

  <tr>
    <td><code>update</code></td>
    <td>key: str, value: dict</td>
    <td>bool</td>
    <td>Updates an existing Redis session and preserves the original TTL.</td>
  </tr>

  <tr>
    <td><code>get</code></td>
    <td>key: str</td>
    <td>dict | None</td>
    <td>
      Retrieves a Redis session value and deserializes it into a Python
      dictionary.
    </td>
  </tr>

  <tr>
    <td><code>check_conf</code></td>
    <td>redis_conf: dict</td>
    <td>None</td>
    <td>Validates presence of required Redis configuration keys.</td>
  </tr>

  <tr>
    <td><code>connect</code></td>
    <td>–</td>
    <td>None</td>
    <td>Initializes the async Redis client with the provided configuration.</td>
  </tr>

  <tr>
    <td><code>serializer</code></td>
    <td>value: any</td>
    <td>str | any</td>
    <td>
      Serializes a dictionary to JSON string; returns value as-is otherwise.
    </td>
  </tr>

  <tr>
    <td><code>deserializer</code></td>
    <td>value: str</td>
    <td>dict | str</td>
    <td>Deserializes a JSON string back into a Python dictionary.</td>
  </tr>

  <tr>
    <td><code>get_all_sessions</code></td>
    <td>–</td>
    <td>list[str]</td>
    <td>Returns a list of all active Redis session keys.</td>
  </tr>

  <tr>
    <td><code>update_orphans_in_sessions</code></td>
    <td>orphan_data: list[dict]</td>
    <td>dict</td>
    <td>
      Moves VMs listed in <code>orphan_data</code> from allowed to orphaned for
      each session.
    </td>
  </tr>

  <tr>
    <td><code>move_vms_from_orphans_to_vms</code></td>
    <td>reactivated_vms: list[str]</td>
    <td>dict</td>
    <td>Moves reactivated VMs from 'orphans' back to the 'vms' list.</td>
  </tr>

  <tr>
    <td><code>rename_vm_in_sessions</code></td>
    <td>renamed_vms: list[dict]</td>
    <td>dict</td>
    <td>
      Renames VM names in both 'vms' and 'orphans' fields across all user
      sessions.
    </td>
  </tr>
</table>

<h3>📄 <code>mongodb.py</code> – MongoDB Interface</h3>
<table border="1" cellpadding="5">
  <tr>
    <th>Function</th>
    <th>Arguments</th>
    <th>Returns</th>
    <th>Description</th>
  </tr>

  <tr>
    <td><code>__init__</code></td>
    <td>mongodb_conf: dict</td>
    <td>None</td>
    <td>Initializes the MongoDB client and loads configuration.</td>
  </tr>

  <tr>
    <td><code>load_config</code></td>
    <td>mongodb_conf: dict</td>
    <td>None</td>
    <td>Validates and sets required MongoDB configuration values.</td>
  </tr>

  <tr>
    <td><code>connect</code></td>
    <td>–</td>
    <td>None</td>
    <td>
      Connects to MongoDB and initializes the database and collection
      references.
    </td>
  </tr>

  <tr>
    <td><code>disconnect</code></td>
    <td>–</td>
    <td>None</td>
    <td>Closes the MongoDB client connection if active.</td>
  </tr>

  <tr>
    <td><code>create</code></td>
    <td>data: dict</td>
    <td>bool</td>
    <td>
      Inserts a new VM document into the collection if it doesn't already exist.
    </td>
  </tr>

  <tr>
    <td><code>get</code></td>
    <td>uuid: str (optional), name: str (optional)</td>
    <td>dict or None</td>
    <td>Fetches a VM by either UUID or name.</td>
  </tr>

  <tr>
    <td><code>update</code></td>
    <td>data: dict</td>
    <td>bool</td>
    <td>Updates an existing VM document based on UUID or name.</td>
  </tr>

  <tr>
    <td><code>delete</code></td>
    <td>data: dict</td>
    <td>bool</td>
    <td>Deletes a VM document from the collection using UUID or name.</td>
  </tr>

  <tr>
    <td><code>get_all_vms_per_host</code></td>
    <td>host_addr: str</td>
    <td>list[dict]</td>
    <td>Returns all VM documents associated with a given ESXi host address.</td>
  </tr>
</table>

<h3>🔁 <code>sync.py</code> – Sync Class</h3>
<p>
  This class handles VM synchronization between ESXi hosts, MongoDB, and Redis.
  It supports VM renaming, orphan tracking, reactivation, and syncing VM states
  periodically or on-demand.
</p>

<table border="1" cellpadding="5">
  <tr>
    <th>Function</th>
    <th>Arguments</th>
    <th>Returns</th>
    <th>Description</th>
  </tr>

  <tr>
    <td><code>__init__</code></td>
    <td>esxi_conf, mongodb_instance, redis_instance, endpoints</td>
    <td>None</td>
    <td>
      Initializes Sync with ESXi credentials, DB/Redis clients, and service
      endpoints.
    </td>
  </tr>

  <tr>
    <td><code>load_config</code></td>
    <td>esxi_conf: dict</td>
    <td>None</td>
    <td>Loads and validates ESXi host configuration.</td>
  </tr>

  <tr>
    <td><code>load_endpoints</code></td>
    <td>endpoints: dict</td>
    <td>None</td>
    <td>Loads and validates dependent service endpoints.</td>
  </tr>

  <tr>
    <td><code>get_service_instance</code></td>
    <td>–</td>
    <td>SmartConnect instance or None</td>
    <td>
      Connects to the ESXi host using pyVmomi and returns the service instance.
    </td>
  </tr>

  <tr>
    <td><code>time_gen</code></td>
    <td>–</td>
    <td>str</td>
    <td>Returns the current timestamp in human-readable format.</td>
  </tr>

  <tr>
    <td><code>rename_handler</code></td>
    <td>renamed_vms: list</td>
    <td>None</td>
    <td>
      Updates Redis sessions and calls external services when VM names are
      changed.
    </td>
  </tr>

  <tr>
    <td><code>compare_changes</code></td>
    <td>db_vm: dict, esxi_vm: dict</td>
    <td>dict</td>
    <td>
      Returns a comparison result including a rename diff (if detected) and
      updated VM data.
    </td>
  </tr>

  <tr>
    <td><code>vm_struct</code></td>
    <td>
      name, hostname, addr, uuid, power_state, vmware_tools, orphan,
      orphan_since
    </td>
    <td>dict</td>
    <td>Builds a VM data structure in the internal format for MongoDB.</td>
  </tr>

  <tr>
    <td><code>get_esxi_vm_list</code></td>
    <td>–</td>
    <td>list[dict]</td>
    <td>Returns a list of VMs from the ESXi host with relevant details.</td>
  </tr>

  <tr>
    <td><code>compare_vms_against_db</code></td>
    <td>esxi_vms: list</td>
    <td>dict</td>
    <td>
      Returns a breakdown of new VMs to add, orphans, and VMs to update based on
      current DB.
    </td>
  </tr>

  <tr>
    <td><code>sync_vms</code></td>
    <td>–</td>
    <td>dict</td>
    <td>
      Performs a full sync cycle with the ESXi host: add, update, orphan,
      rename, and reactivation logic.
    </td>
  </tr>

  <tr>
    <td><code>sync_selected_vms</code></td>
    <td>vm_ids: list</td>
    <td>dict</td>
    <td>Performs a sync operation only for selected VMs by UUID or name.</td>
  </tr>
</table>

<h3>🌐 <code>server.py</code> – APIServer Class</h3>
<p>
  This class defines and serves the FastAPI-based web server. It exposes
  endpoints for checking sync status, forcing sync operations, and syncing
  selected VMs manually.
</p>

<table border="1" cellpadding="5">
  <tr>
    <th>Function</th>
    <th>Arguments</th>
    <th>Returns</th>
    <th>Description</th>
  </tr>

  <tr>
    <td><code>__init__</code></td>
    <td>server_conf, sync_status_getter, force_sync_trigger, sync_instances</td>
    <td>None</td>
    <td>Initializes the FastAPI server with routes and sync logic hooks.</td>
  </tr>

  <tr>
    <td><code>make_response</code></td>
    <td>ok: bool, message: str, **kwargs</td>
    <td><code>JSONResponse</code></td>
    <td>Generates a consistent JSON response format.</td>
  </tr>

  <tr>
    <td><code>load_config</code></td>
    <td>server_conf: dict</td>
    <td>None</td>
    <td>Loads required host and port configuration for the API server.</td>
  </tr>

  <tr>
    <td><code>register_routes</code></td>
    <td>–</td>
    <td>None</td>
    <td>
      Registers all FastAPI endpoints including sync status, manual trigger, and
      selected sync.
    </td>
  </tr>

  <tr>
    <td><code>GET /sync/status</code></td>
    <td>–</td>
    <td>JSONResponse</td>
    <td>Returns whether a sync process is currently running.</td>
  </tr>

  <tr>
    <td><code>GET /sync/now</code></td>
    <td>–</td>
    <td>JSONResponse</td>
    <td>Triggers an immediate sync unless one is already in progress.</td>
  </tr>

  <tr>
    <td><code>POST /sync/vms</code></td>
    <td><code>SyncVMs</code> payload</td>
    <td>JSONResponse</td>
    <td>Triggers a sync for selected VMs by name or UUID.</td>
  </tr>

  <tr>
    <td><code>run</code></td>
    <td>–</td>
    <td>None</td>
    <td>
      Starts the FastAPI server using uvicorn with the configured host and port.
    </td>
  </tr>
</table>

<hr />

<h2 id="api-documentation">🧪 API Documentation</h2>
<ul>
  <li>📘 <strong>Postman Collection</strong>: <em>(link to be added)</em></li>
  <li>
    📘 <strong>Swagger UI</strong>: Accessible at <code>/docs</code> while
    server is running
  </li>
</ul>

<hr />

<h2 id="notes">📝 Notes</h2>
<ul>
  <li>
    Redis session keys are 30-character random alphanumeric strings used as
    unique session identifiers.
  </li>
  <li>
    Each user session contains a list of <code>vms</code> and
    <code>orphans</code>.
  </li>
  <li>
    Orphaned VMs are moved from <code>vms</code> to <code>orphans</code> when
    they no longer appear in ESXi.
  </li>
  <li>
    Format of orphaned VMs in the session:
    <pre><code>[
  {
    "name": "vm-01",
    "since": "01-07-2024: 12:34:00"
  }
]</code></pre>
  </li>
</ul>

<hr />

<h2 id="future-enhancements">🔮 Future Enhancements</h2>
<ul>
  <li>📊 Add centralized logging via a log service or ELK stack integration</li>
  <li>
    🧪 Add more test coverage and auto-validation for sync scenarios and edge
    cases
  </li>
</ul>
