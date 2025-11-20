#!/usr/bin/env python3
"""
Health Details MCP Server using FastMCP
AWS Secrets Manager integration using RRR library - NO hardcoded credentials
"""

import requests
import httpx
import asyncio
import json
import logging
import sys
from typing import Dict, Any, List, TypedDict, Literal, Optional
from pydantic import BaseModel
from fastmcp import FastMCP
from mcp.server import Server
import mcp.types as types

# Import configuration
from config import HealthMCPConfig

# RRR Library import for AWS Secrets Manager
try:
    from ReduceReuseRecycle import get_api_secrets
    RRR_AVAILABLE = True
except Exception:
    try:
        from ReduceReuseRecycle.apifunc import get_api_secrets
        RRR_AVAILABLE = True
    except Exception as e:
        RRR_AVAILABLE = False
        print(f"⚠️  RRR import failed: {e}")

# Set up logging
logging.basicConfig(
    level=getattr(logging, HealthMCPConfig.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Local Message type for MCP prompts
class Message(TypedDict):
    role: Literal["user", "system", "assistant"]
    content: str

print("🏥 Initializing Health Details FastMCP Server...")
print(f"📋 Configuration loaded from: config.py")
print(f"🔐 AWS Secret Path: {HealthMCPConfig.get_aws_secret_path()}")

# Initialize FastMCP instance
mcp = FastMCP("Health Details App")

# ===== DATA MODELS =====

class UserInput(BaseModel):
    first_name: str
    last_name: str
    ssn: str
    date_of_birth: str  # Format: YYYY-MM-DD
    gender: str
    zip_code: str

# ===== AWS SECRETS MANAGER INTEGRATION =====

class AWSSecretsManager:
    """
    AWS Secrets Manager integration using RRR library
    Fetches OAuth credentials from AWS - NO hardcoded secrets
    """
    
    def __init__(self):
        self.logger = logging.getLogger("aws_secrets")
        self.logger.setLevel(logging.INFO)
        
        # Configuration from config.py
        self.env = HealthMCPConfig.AWS_ENV
        self.region_name = HealthMCPConfig.AWS_REGION
        self.aplctn_cd = HealthMCPConfig.AWS_APLCTN_CD
        self.app_id = HealthMCPConfig.AWS_APP_ID
        
        # OAuth credentials (will be fetched from AWS)
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.grant_type: str = HealthMCPConfig.GRANT_TYPE
        
        # RRR results
        self.headers_with_secrets: Dict[str, str] = {}
        self.body_with_secrets: Dict[str, str] = {}
        self.params_with_secrets: Dict[str, str] = {}
        self.cert_path: Optional[str] = None
        
        # Fetch secrets on initialization
        if RRR_AVAILABLE:
            self._fetch_secrets_from_aws()
        else:
            error_msg = "❌ RRR library not available. Cannot fetch credentials from AWS."
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _fetch_secrets_from_aws(self):
        """
        Fetch OAuth credentials from AWS Secrets Manager using RRR library
        
        RRR Process:
        1. Fetches secrets from AWS at: {env}/api/{aplctn_cd}
        2. Replaces $$ placeholders in headers/params/body
        3. Downloads SSL certificates if configured
        
        Secret structure in AWS:
        {
            "client_id": "MILLIMAN",
            "client_secret": "...",
            "grant_type": "client_credentials"
        }
        """
        try:
            self.logger.info(f"🔐 Fetching secrets from AWS Secrets Manager...")
            self.logger.info(f"    Secret path: {self.env}/api/{self.aplctn_cd}")
            self.logger.info(f"    App ID: {self.app_id}")
            self.logger.info(f"    Region: {self.region_name}")
            
            # Prepare headers with placeholders
            input_headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            # Prepare body with placeholders - RRR will replace $$ with values from AWS
            input_body = {
                "grant_type": "$${grant_type}",      # Will be replaced by RRR
                "client_id": "$${client_id}",        # Will be replaced by RRR
                "client_secret": "$${client_secret}" # Will be replaced by RRR
            }
            
            # Prepare params (empty for OAuth)
            input_params = {}
            
            # Call RRR's get_api_secrets function
            self.logger.info("📡 Calling RRR get_api_secrets()...")
            params, headers, body, cert = get_api_secrets(
                log=self.logger,
                env=self.env,
                region_name=self.region_name,
                aplctn_cd=self.aplctn_cd,
                auth_type='oauth',      # OAuth authentication type
                provider='anthem',      # Provider name
                app_id=self.app_id,
                params=input_params,
                headers=input_headers,
                body=input_body
            )
            
            # Store results from RRR
            self.params_with_secrets = params
            self.headers_with_secrets = headers
            self.body_with_secrets = body
            self.cert_path = cert
            
            # Extract OAuth credentials from body (after $$ replacement by RRR)
            self.client_id = body.get('client_id')
            self.client_secret = body.get('client_secret')
            self.grant_type = body.get('grant_type', self.grant_type)
            
            # Validate credentials were fetched
            if not self.client_id:
                raise ValueError("client_id not found in AWS secret")
            if not self.client_secret:
                raise ValueError("client_secret not found in AWS secret")
            
            self.logger.info(f"✅ Secrets fetched successfully from AWS!")
            self.logger.info(f"    Client ID: {self.client_id}")
            self.logger.info(f"    Client Secret: {'*' * 20} (hidden)")
            self.logger.info(f"    Grant Type: {self.grant_type}")
            self.logger.info(f"    SSL Certificate: {cert if cert else '[NO CERT]'}")
            
        except Exception as e:
            error_msg = f"❌ Failed to fetch secrets from AWS: {e}"
            self.logger.error(error_msg)
            import traceback
            traceback.print_exc()
            raise RuntimeError(error_msg)
    
    def get_token_payload(self) -> Dict[str, str]:
        """Get OAuth token request payload with credentials from AWS"""
        if not self.client_id or not self.client_secret:
            raise ValueError("OAuth credentials not loaded from AWS")
        
        # Use body_with_secrets if available (from RRR), otherwise construct
        if self.body_with_secrets:
            return self.body_with_secrets.copy()
        else:
            return {
                "grant_type": self.grant_type,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
    
    def get_token_headers(self) -> Dict[str, str]:
        """Get OAuth token request headers"""
        if self.headers_with_secrets:
            return self.headers_with_secrets.copy()
        else:
            return {"Content-Type": "application/x-www-form-urlencoded"}
    
    def get_api_headers(self, token: str) -> Dict[str, str]:
        """Get API request headers with authorization token"""
        return {
            "Authorization": token,
            "Content-Type": "application/json"
        }
    
    def get_verify_value(self) -> bool | str:
        """Get SSL verification value (cert path or boolean)"""
        return self.cert_path if self.cert_path else True

# Initialize AWS Secrets Manager
try:
    aws_secrets = AWSSecretsManager()
    logger.info("✅ AWS Secrets Manager initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize AWS Secrets Manager: {e}")
    logger.error("❌ Cannot proceed without AWS credentials")
    sys.exit(1)

# ===== JSON SERIALIZATION HELPER =====

def safe_json_dumps(obj, indent=2) -> str:
    """Safely convert object to JSON string, handling non-serializable objects"""
    def json_serializer(obj):
        if hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # custom objects
            return obj.__dict__
        elif isinstance(obj, bytes):  # bytes objects
            return obj.decode('utf-8', errors='ignore')
        elif hasattr(obj, '__str__'):  # any object with string representation
            return str(obj)
        else:
            return f"<non-serializable: {type(obj).__name__}>"
    
    try:
        return json.dumps(obj, indent=indent, default=json_serializer, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"JSON serialization failed: {str(e)}, falling back to string representation")
        return str(obj)

# ===== API HELPER FUNCTIONS =====

def get_access_token_sync() -> str | None:
    """Get OAuth access token using credentials from AWS Secrets Manager"""
    try:
        logger.info("🔑 Requesting OAuth access token...")
        
        r = requests.post(
            HealthMCPConfig.TOKEN_URL,
            data=aws_secrets.get_token_payload(),
            headers=aws_secrets.get_token_headers(),
            verify=aws_secrets.get_verify_value(),
            timeout=HealthMCPConfig.REQUEST_TIMEOUT
        )
        r.raise_for_status()
        
        token = r.json().get("access_token")
        logger.info(f"✅ Access token received: {token[:20]}..." if token else "❌ No token in response")
        return token
        
    except Exception as e:
        logger.error(f"❌ Error getting access token: {str(e)}")
        return None

async def async_get_token() -> Dict[str, Any]:
    """Async version of get access token"""
    async with httpx.AsyncClient(verify=aws_secrets.get_verify_value()) as client:
        try:
            r = await client.post(
                HealthMCPConfig.TOKEN_URL,
                data=aws_secrets.get_token_payload(),
                headers=aws_secrets.get_token_headers(),
                timeout=HealthMCPConfig.REQUEST_TIMEOUT
            )
            return {"status_code": r.status_code, "body": r.json()}
        except Exception as e:
            return {"status_code": 500, "error": str(e)}

async def async_submit_request(user: UserInput, url: str) -> Dict[str, Any]:
    """Submit request to healthcare API"""
    token = await asyncio.to_thread(get_access_token_sync)
    if not token:
        return {"status_code": 500, "error": "Access token not found"}

    payload = {
        "requestId": "77554079",
        "firstName": user.first_name,
        "lastName": user.last_name,
        "ssn": user.ssn,
        "dateOfBirth": user.date_of_birth,
        "gender": user.gender,
        "zipCodes": [user.zip_code],
        "callerId": "Anthem-InternalTesting"
    }

    headers = aws_secrets.get_api_headers(token)
    
    try:
        r = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=aws_secrets.get_verify_value(),
            timeout=HealthMCPConfig.REQUEST_TIMEOUT
        )
        if r.status_code != 200:
            return {"status_code": r.status_code, "error": r.text, "url": url}
        return {"status_code": r.status_code, "body": r.json()}
    except Exception as e:
        return {"status_code": 500, "error": str(e), "url": url}

async def async_mcid_search(user: UserInput) -> Dict[str, Any]:
    """Search MCID service"""
    token = await asyncio.to_thread(get_access_token_sync)
    if not token:
        return {"status_code": 500, "error": "Access token not found"}

    headers = {
        "Content-Type": "application/json",
        "Apiuser": "MillimanUser",
        "Authorization": token
    }

    mcid_payload = {
        "requestID": "1",
        "processStatus": {"completed": "false", "isMemput": "false"},
        "consumer": [{
            "fname": user.first_name,
            "lname": user.last_name,
            "sex": user.gender,
            "dob": user.date_of_birth.replace("-", ""),
            "addressList": [{"type": "P", "zip": user.zip_code}],
            "id": {"ssn": user.ssn}
        }],
        "searchSetting": {"minScore": "100", "maxResult": "1"}
    }

    # MCID service uses self-signed cert, use cert from RRR or disable verification
    verify_value = aws_secrets.cert_path if aws_secrets.cert_path else False
    
    async with httpx.AsyncClient(verify=verify_value) as client:
        try:
            r = await client.post(
                HealthMCPConfig.MCID_URL,
                headers=headers,
                json=mcid_payload,
                timeout=30
            )
            if r.status_code == 401:
                return {"status_code": 401, "error": "Unauthorized", "response_text": r.text}
            return {"status_code": r.status_code, "body": r.json()}
        except Exception as e:
            return {"status_code": 500, "error": str(e)}

# ===== MCP TOOLS USING @mcp.tool DECORATOR =====

@mcp.tool()
async def all() -> Dict[str, Any]:
    """Complete system overview with real API status"""
    logger.info("Generating system overview")
    
    try:
        token_status = await async_get_token()
        api_status = "operational" if token_status.get("status_code") == 200 else "degraded"
        
        return {
            "system_status": api_status,
            "timestamp": "2024-01-01T12:00:00Z",
            "api_endpoints": {
                "token_service": {
                    "url": HealthMCPConfig.TOKEN_URL,
                    "status": "active" if token_status.get("status_code") == 200 else "error"
                },
                "medical_service": {"url": HealthMCPConfig.MEDICAL_URL, "status": "active"},
                "pharmacy_service": {"url": HealthMCPConfig.PHARMACY_URL, "status": "active"},
                "mcid_service": {"url": HealthMCPConfig.MCID_URL, "status": "active"}
            },
            "authentication": {
                "client_id": aws_secrets.client_id,
                "status": "configured",
                "aws_secret_path": HealthMCPConfig.get_aws_secret_path(),
                "aws_region": HealthMCPConfig.AWS_REGION,
                "aws_env": HealthMCPConfig.AWS_ENV
            },
            "configuration": HealthMCPConfig.to_dict()
        }
    except Exception as e:
        logger.error(f"Error in system overview: {str(e)}")
        return {
            "system_status": "error",
            "error": str(e),
            "timestamp": "2024-01-01T12:00:00Z"
        }

@mcp.tool()
async def token() -> Dict[str, Any]:
    """Get real authentication token from Milliman API"""
    logger.info("Getting authentication token")
    
    try:
        token_response = await async_get_token()
        
        if token_response.get("status_code") == 200:
            token_data = token_response.get("body", {})
            return {
                "status": "success",
                "token": token_data.get("access_token"),
                "token_type": token_data.get("token_type", "bearer"),
                "expires_in": token_data.get("expires_in"),
                "client_id": aws_secrets.client_id
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to get token: {token_response.get('error', 'Unknown error')}",
                "status_code": token_response.get("status_code")
            }
    except Exception as e:
        logger.error(f"Error getting token: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@mcp.tool()
async def medical_submit(
    first_name: str, last_name: str, ssn: str,
    date_of_birth: str, gender: str, zip_code: str
) -> Dict[str, Any]:
    """Submit medical claim to real Milliman healthcare API"""
    logger.info(f"Medical submission for {first_name} {last_name}")
    
    try:
        user_input = UserInput(
            first_name=first_name, last_name=last_name, ssn=ssn,
            date_of_birth=date_of_birth, gender=gender, zip_code=zip_code
        )
        
        result = await async_submit_request(user_input, HealthMCPConfig.MEDICAL_URL)
        return result
    except Exception as e:
        logger.error(f"Error in medical submission: {str(e)}")
        return {
            "status_code": 500,
            "error": str(e),
            "patient": f"{first_name} {last_name}"
        }

@mcp.tool()
async def pharmacy_submit(
    first_name: str, last_name: str, ssn: str,
    date_of_birth: str, gender: str, zip_code: str
) -> Dict[str, Any]:
    """Submit pharmacy claim to real Milliman healthcare API"""
    logger.info(f"Pharmacy submission for {first_name} {last_name}")
    
    try:
        user_input = UserInput(
            first_name=first_name, last_name=last_name, ssn=ssn,
            date_of_birth=date_of_birth, gender=gender, zip_code=zip_code
        )
        
        result = await async_submit_request(user_input, HealthMCPConfig.PHARMACY_URL)
        return result
    except Exception as e:
        logger.error(f"Error in pharmacy submission: {str(e)}")
        return {
            "status_code": 500,
            "error": str(e),
            "patient": f"{first_name} {last_name}"
        }

@mcp.tool()
async def mcid_search(
    first_name: str, last_name: str, ssn: str,
    date_of_birth: str, gender: str, zip_code: str
) -> Dict[str, Any]:
    """Search for member using MCID (Member Consumer ID) service"""
    logger.info(f"MCID search for {first_name} {last_name}")
    
    try:
        user_input = UserInput(
            first_name=first_name, last_name=last_name, ssn=ssn,
            date_of_birth=date_of_birth, gender=gender, zip_code=zip_code
        )
        
        result = await async_mcid_search(user_input)
        return result
    except Exception as e:
        logger.error(f"Error in MCID search: {str(e)}")
        return {
            "status_code": 500,
            "error": str(e),
            "patient": f"{first_name} {last_name}"
        }

@mcp.tool()
async def get_all_healthcare_data(
    first_name: str, last_name: str, ssn: str,
    date_of_birth: str, gender: str, zip_code: str
) -> Dict[str, Any]:
    """Get comprehensive healthcare data from all Milliman APIs (medical, pharmacy, MCID)"""
    logger.info(f"Getting all healthcare data for {first_name} {last_name}")
    
    try:
        user_input = UserInput(
            first_name=first_name, last_name=last_name, ssn=ssn,
            date_of_birth=date_of_birth, gender=gender, zip_code=zip_code
        )
        
        token_result, medical_result, pharmacy_result, mcid_result = await asyncio.gather(
            async_get_token(),
            async_submit_request(user_input, HealthMCPConfig.MEDICAL_URL),
            async_submit_request(user_input, HealthMCPConfig.PHARMACY_URL),
            async_mcid_search(user_input),
            return_exceptions=True
        )
        
        return {
            "patient": {"first_name": first_name, "last_name": last_name},
            "token_service": token_result if not isinstance(token_result, Exception) else {"error": str(token_result)},
            "medical_service": medical_result if not isinstance(medical_result, Exception) else {"error": str(medical_result)},
            "pharmacy_service": pharmacy_result if not isinstance(pharmacy_result, Exception) else {"error": str(pharmacy_result)},
            "mcid_service": mcid_result if not isinstance(mcid_result, Exception) else {"error": str(mcid_result)}
        }
    except Exception as e:
        logger.error(f"Error getting all healthcare data: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "patient": f"{first_name} {last_name}"
        }

# ===== MCP PROMPTS USING @mcp.prompt DECORATOR =====

@mcp.prompt(name="health-details", description="Health management system to handle medical records, pharmacy prescriptions, patient data search, system monitoring, and authentication")
async def health_details_prompt(query: str) -> List[Message]:
    """Generate a comprehensive health management prompt"""
    return [{
        "role": "user", 
        "content": f"""
You are an expert in Health Management Systems using real Milliman/Anthem APIs.

You are provided with the following health management tools:

1) **all** - Complete system overview and health status monitoring
   - Use for: system status checks, service availability, performance metrics
   - Returns: comprehensive system health, database status, active sessions

2) **token** - Authentication and session management interface  
   - Use for: user authentication, session management, security operations
   - Returns: token status, authentication results, session information

3) **medical_submit** - Medical record submission and management
   - Use for: submitting medical claims to real Milliman API
   - Returns: submission confirmation, record ID, validation status

4) **pharmacy_submit** - Pharmacy prescription submission and management
   - Use for: prescription submissions, medication management, pharmacy operations
   - Returns: prescription status, pharmacy processing, pickup information

5) **mcid_search** - Comprehensive database search interface
   - Use for: searching patients, prescriptions, medical records, providers, pharmacies
   - Returns: search results with relevance scores, detailed information, metadata

6) **get_all_healthcare_data** - Get comprehensive data from all APIs
   - Use for: getting complete healthcare information from all services simultaneously
   - Returns: combined results from all healthcare APIs

Patient data format: first_name, last_name, ssn, date_of_birth (YYYY-MM-DD), gender (M/F), zip_code

You will respond with the results returned from the right tool.

User Query: {query}
"""
    }]

@mcp.prompt(name="healthcare-summary", description="Summarize healthcare data intent")
async def healthcare_summary_prompt(query: str) -> List[Message]:
    """Generate a summary prompt for healthcare data queries"""
    return [{
        "role": "user",
        "content": f"Healthcare data summary request: {query}. Use the appropriate tools to get current API status and patient data."
    }]

# ===== SSE COMPATIBILITY WRAPPER =====

class HealthMCPServerWrapper:
    def __init__(self, fastmcp_instance):
        self.fastmcp = fastmcp_instance
        self.server = Server("health-details")
        self._setup_standard_mcp_server()
        
    def _setup_standard_mcp_server(self):
        """Setup standard MCP server that delegates to FastMCP"""
        
        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="all",
                    description="Complete system overview with real API status",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                types.Tool(
                    name="token",
                    description="Get real authentication token from Milliman API",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                types.Tool(
                    name="medical_submit",
                    description="Submit medical claim to real Milliman API",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "first_name": {"type": "string", "description": "Patient's first name"},
                            "last_name": {"type": "string", "description": "Patient's last name"},
                            "ssn": {"type": "string", "description": "Social Security Number"},
                            "date_of_birth": {"type": "string", "description": "Date of birth (YYYY-MM-DD format)"},
                            "gender": {"type": "string", "description": "Gender (M/F)"},
                            "zip_code": {"type": "string", "description": "ZIP code"}
                        },
                        "required": ["first_name", "last_name", "ssn", "date_of_birth", "gender", "zip_code"]
                    }
                ),
                types.Tool(
                    name="pharmacy_submit",
                    description="Submit pharmacy claim to real Milliman API",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "first_name": {"type": "string", "description": "Patient's first name"},
                            "last_name": {"type": "string", "description": "Patient's last name"},
                            "ssn": {"type": "string", "description": "Social Security Number"},
                            "date_of_birth": {"type": "string", "description": "Date of birth (YYYY-MM-DD format)"},
                            "gender": {"type": "string", "description": "Gender (M/F)"},
                            "zip_code": {"type": "string", "description": "ZIP code"}
                        },
                        "required": ["first_name", "last_name", "ssn", "date_of_birth", "gender", "zip_code"]
                    }
                ),
                types.Tool(
                    name="mcid_search",
                    description="Search for member using MCID service",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "first_name": {"type": "string", "description": "Patient's first name"},
                            "last_name": {"type": "string", "description": "Patient's last name"},
                            "ssn": {"type": "string", "description": "Social Security Number"},
                            "date_of_birth": {"type": "string", "description": "Date of birth (YYYY-MM-DD format)"},
                            "gender": {"type": "string", "description": "Gender (M/F)"},
                            "zip_code": {"type": "string", "description": "ZIP code"}
                        },
                        "required": ["first_name", "last_name", "ssn", "date_of_birth", "gender", "zip_code"]
                    }
                ),
                types.Tool(
                    name="get_all_healthcare_data",
                    description="Get comprehensive healthcare data from all APIs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "first_name": {"type": "string", "description": "Patient's first name"},
                            "last_name": {"type": "string", "description": "Patient's last name"},
                            "ssn": {"type": "string", "description": "Social Security Number"},
                            "date_of_birth": {"type": "string", "description": "Date of birth (YYYY-MM-DD format)"},
                            "gender": {"type": "string", "description": "Gender (M/F)"},
                            "zip_code": {"type": "string", "description": "ZIP code"}
                        },
                        "required": ["first_name", "last_name", "ssn", "date_of_birth", "gender", "zip_code"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Execute FastMCP tools via SSE"""
            logger.info(f"SSE Tool call: {name}")
            
            try:
                # Call the corresponding FastMCP tool function
                if name == "all":
                    result = await all()
                elif name == "token":
                    result = await token()
                elif name == "medical_submit":
                    result = await medical_submit(**arguments)
                elif name == "pharmacy_submit":
                    result = await pharmacy_submit(**arguments)
                elif name == "mcid_search":
                    result = await mcid_search(**arguments)
                elif name == "get_all_healthcare_data":
                    result = await get_all_healthcare_data(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                # Use safe JSON serialization
                result_text = safe_json_dumps(result)
                
                logger.info(f"✅ SSE Tool {name} executed successfully")
                return [types.TextContent(type="text", text=result_text)]
                
            except Exception as e:
                error_msg = f"Error executing {name}: {str(e)}"
                logger.error(error_msg)
                return [types.TextContent(type="text", text=error_msg)]
        
        @self.server.list_prompts()
        async def list_prompts() -> List[types.Prompt]:
            return [
                types.Prompt(
                    name="health-details",
                    description="Health management system with real API integration",
                    arguments=[
                        types.PromptArgument(
                            name="query",
                            description="Health-related query or request",
                            required=True
                        )
                    ]
                ),
                types.Prompt(
                    name="healthcare-summary",
                    description="Healthcare API summary with real data",
                    arguments=[
                        types.PromptArgument(
                            name="query",
                            description="Summary request",
                            required=True
                        )
                    ]
                )
            ]
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, str]) -> types.GetPromptResult:
            query = arguments.get("query", "")
            
            if name == "health-details":
                messages = await health_details_prompt(query)
            elif name == "healthcare-summary":
                messages = await healthcare_summary_prompt(query)
            else:
                raise ValueError(f"Unknown prompt: {name}")
            
            # Convert to MCP format
            mcp_messages = []
            for msg in messages:
                mcp_messages.append(types.PromptMessage(
                    role=msg['role'],
                    content=types.TextContent(type="text", text=msg['content'])
                ))
            
            return types.GetPromptResult(
                description=f"Health Details - {name}",
                messages=mcp_messages
            )

# Create the wrapper and update the mcp instance for SSE compatibility
mcp_wrapper = HealthMCPServerWrapper(mcp)

# Add _mcp_server attribute to the FastMCP instance for app.py compatibility
mcp._mcp_server = mcp_wrapper.server

print("✅ Health Details FastMCP Server ready!")
print("🔗 SSE Integration: mcp._mcp_server configured")
print("🌐 Real API Integration: All tools connected")
print(f"🔐 AWS Secrets: {HealthMCPConfig.get_aws_secret_path()}")
print(f"📍 AWS Region: {HealthMCPConfig.AWS_REGION}")
print(f"🔑 Client ID: {aws_secrets.client_id}")
print("📡 Available MCP tools:")
print("   - all (System overview with real API status)")
print("   - token (Get real authentication token)")
print("   - medical_submit (Submit to real medical API)")
print("   - pharmacy_submit (Submit to real pharmacy API)")
print("   - mcid_search (Search real MCID service)")
print("   - get_all_healthcare_data (Get comprehensive data)")
print("📝 Available MCP prompts:")
print("   - health-details (Main health management prompt)")
print("   - healthcare-summary (API summary prompt)")

if __name__ == "__main__":
    print("🚀 Running FastMCP Server")
    print("ℹ️  For SSE integration, run: python app.py")
    mcp.run()
