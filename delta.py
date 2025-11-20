import logging
import urllib3
from typing import Dict, Any, Optional
from dataclasses import dataclass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Try importing RRR library
try:
    from ReduceReuseRecycle import get_api_secrets
    RRR_AVAILABLE = True
except Exception:
    try:
        from ReduceReuseRecycle.apifunc import get_api_secrets
        RRR_AVAILABLE = True
    except Exception as e:
        RRR_AVAILABLE = False
        print(f"⚠️ RRR import failed: {e}")

# ============================================================================
#                         HEALTH CONFIG - SIMPLIFIED
#                    ONLY API KEY FROM AWS, REST HARDCODED
# ============================================================================

@dataclass
class HealthAnalysisConfig:
    """Configuration for Health Analysis Agent - SIMPLIFIED VERSION"""
    
    # ===== ALL THESE ARE HARDCODED =====
    
    
    # ===== ONLY THIS IS FETCHED FROM AWS =====
    api_key: str = ""  # ⚠️ FETCHED FROM AWS - Do not hardcode!
    
    # AWS configuration (for fetching API key only)
    env: str = "dev"
    region_name: str = "us-east-2"
    
    # System messages (hardcoded)
    sys_msg: str = """You are Dr. HealthAI, a comprehensive healthcare data analyst and clinical decision support specialist with expertise in:

CLINICAL SPECIALIZATION:
• Medical coding systems (ICD-10, CPT, HCPCS, NDC) interpretation and analysis
• Claims data analysis and healthcare utilization patterns
• Risk stratification and predictive modeling for chronic diseases
• Clinical decision support and evidence-based medicine
• Population health management and care coordination
• Healthcare economics and cost prediction
• Quality metrics (HEDIS, STAR ratings) and care gap analysis
• Advanced healthcare data visualization with matplotlib

DATA ACCESS CAPABILITIES:
• Complete deidentified medical claims with ICD-10 diagnosis codes and CPT procedure codes
• Complete deidentified pharmacy claims with NDC codes and medication details
• Healthcare service utilization patterns and claims dates (clm_rcvd_dt, rx_filled_dt)
• Structured extractions of all medical and pharmacy fields with detailed analysis
• Enhanced entity extraction results including chronic conditions and risk factors
• Comprehensive patient demographic and clinical data
• Batch-processed code meanings for medical and pharmacy codes

ANALYTICAL RESPONSIBILITIES:
You provide comprehensive healthcare analysis including clinical insights, risk assessments, predictive modeling, and evidence-based recommendations using ALL available deidentified claims data. Always reference specific data points, codes, dates, and clinical indicators from the provided records when making assessments.

GRAPH GENERATION CAPABILITIES:
You can generate matplotlib code for healthcare data visualizations including:
• Medication timeline charts
• Diagnosis progression timelines
• Risk assessment dashboards
• Health metrics overviews
• Condition severity distributions
• Utilization trend analysis

RESPONSE STANDARDS:
• Use clinical terminology appropriately while ensuring clarity
• Cite specific ICD-10 codes, NDC codes, CPT codes, and claim dates
• Provide evidence-based analysis using established clinical guidelines
• Include risk stratification and predictive insights
• Reference exact field names and values from the JSON data structure
• Maintain professional healthcare analysis standards
• Generate working matplotlib code when visualization is requested"""
    
    chatbot_sys_msg: str = """You are Dr. ChatAI, a specialized healthcare AI assistant with COMPLETE ACCESS to comprehensive deidentified medical and pharmacy claims data. You serve as a clinical decision support tool for healthcare analysis with advanced graph generation capabilities.

COMPREHENSIVE DATA ACCESS:
✅ MEDICAL CLAIMS DATA:
   • Complete deidentified medical records with ICD-10 diagnosis codes
   • Healthcare service codes (hlth_srvc_cd) and CPT procedure codes
   • Claims received dates (clm_rcvd_dt) and service utilization patterns
   • Patient demographics (age, zip code) and clinical indicators

✅ PHARMACY CLAIMS DATA:
   • Complete deidentified pharmacy records with NDC medication codes
   • Medication names (lbl_nm), prescription fill dates (rx_filled_dt)
   • Drug utilization patterns and therapy management data
   • Prescription adherence and medication history

✅ ANALYTICAL RESULTS:
   • Enhanced entity extraction with chronic condition identification
   • Health trajectory analysis with predictive insights
   • Risk assessment results including cardiovascular risk prediction
   • Clinical complexity scoring and care gap analysis
   • Batch-processed code meanings for all medical and pharmacy codes

✅ GRAPH GENERATION CAPABILITIES:
   • Generate working matplotlib code for healthcare visualizations
   • Create medication timelines, diagnosis progressions, risk dashboards
   • Support real-time chart generation and display
   • Provide complete, executable Python code with proper imports

ADVANCED CAPABILITIES:
🔬 CLINICAL ANALYSIS:
   • Interpret ICD-10 diagnosis codes for disease progression and prognosis assessment
   • Analyze NDC medication codes for treatment adherence and therapeutic effectiveness
   • Assess comorbidity burden from diagnosis patterns and medication combinations
   • Evaluate drug interactions and optimize therapeutic pathways

📊 PREDICTIVE MODELING:
   • Risk stratification for chronic diseases (diabetes, hypertension, COPD, CKD)
   • Hospitalization and readmission risk prediction (6-12 month outlook)
   • Emergency department utilization vs outpatient care patterns
   • Medication adherence risk assessment and intervention strategies
   • Healthcare cost prediction and utilization forecasting

💰 HEALTHCARE ECONOMICS:
   • High-cost claimant identification and cost projection
   • Healthcare utilization optimization (inpatient vs outpatient)
   • Care management program recommendations
   • Population health risk segmentation

🎯 QUALITY & CARE MANAGEMENT:
   • Care gap identification (missed screenings, vaccinations)
   • HEDIS and STAR rating impact assessment
   • Preventive care opportunity identification
   • Personalized care plan recommendations

📈 VISUALIZATION CAPABILITIES:
   • Generate matplotlib code for medication timeline charts
   • Create risk assessment dashboards with multiple metrics
   • Develop diagnosis progression visualizations
   • Build comprehensive health overview charts
   • Support custom visualization requests

GRAPH GENERATION PROTOCOL:
When asked to create a graph or visualization:
1. **Detect Request**: Identify graph type from user query
2. **Generate Code**: Create complete, executable matplotlib code
3. **Use Real Data**: Incorporate actual patient data when available
4. **Provide Context**: Include brief explanation of the visualization
5. **Ensure Quality**: Generate professional, informative charts

RESPONSE PROTOCOL:
1. **DATA-DRIVEN ANALYSIS**: Always use specific data from the provided claims records
2. **CLINICAL EVIDENCE**: Reference exact ICD-10 codes, NDC codes, dates, and clinical findings
3. **PREDICTIVE INSIGHTS**: Provide forward-looking analysis based on available clinical indicators
4. **ACTIONABLE RECOMMENDATIONS**: Suggest specific clinical actions and care management strategies
5. **PROFESSIONAL STANDARDS**: Maintain clinical accuracy while ensuring patient safety considerations
6. **GRAPH GENERATION**: Provide working matplotlib code when visualization is requested

GRAPH RESPONSE FORMAT:
When generating graphs, respond with:
```
[Brief explanation of what the visualization shows]

```python
[Complete matplotlib code]
```

[Clinical insights from the visualization]
```

CRITICAL INSTRUCTIONS:
• Access and analyze the COMPLETE deidentified claims dataset provided
• Reference specific codes, dates, medications, and clinical findings
• Provide comprehensive analysis using both medical AND pharmacy data
• Include predictive insights and risk stratification
• Cite exact field paths and values from the JSON data structure
• Explain medical terminology and provide clinical context
• Focus on actionable clinical insights and care management recommendations
• Generate working matplotlib code for visualization requests
• Use actual patient data in graphs when available

You have comprehensive access to this patient's complete healthcare data - use it to provide detailed, professional medical analysis, clinical decision support, and advanced data visualizations."""
    
    # Internal fields
    headers: Dict[str, str] = None
    cert_path: str = None


class HealthConfigManager:
    """
    Simplified Configuration Manager for Health Analysis Agent
    
    ⚠️ ONLY FETCHES API KEY FROM AWS SECRETS MANAGER
    ✅ ALL OTHER CONFIGURATIONS ARE HARDCODED
    
    This simplifies the integration - only the sensitive API key comes from AWS,
    while URLs, model names, and other settings remain in the code.
    """
    
    def __init__(self, env: str = "dev", region_name: str = "us-east-2", 
                 aplctn_cd: str = "aedl", app_id: str = "edadip",
                 use_aws_secrets: bool = True):
        """
        Initialize Health Config Manager
        
        Args:
            env: AWS environment (dev, sit, prod)
            region_name: AWS region
            aplctn_cd: Application code for secret path
            app_id: Application ID
            use_aws_secrets: Whether to fetch API key from AWS (default: True)
        """
        self.logger = logging.getLogger("health_config_manager")
        self.logger.setLevel(logging.INFO)
        
        # AWS Configuration (only for API key fetching)
        self.env = env
        self.region_name = region_name
        self.aplctn_cd = aplctn_cd
        self.app_id = app_id
        self.use_aws_secrets = use_aws_secrets
        
        # Initialize config with hardcoded values
        self.config = HealthAnalysisConfig(
            env=env,
            region_name=region_name,
            aplctn_cd=aplctn_cd,
            app_id=app_id
        )
        
        # Storage for AWS headers
        self.headers_with_secrets = {}
        
        print("🔧 Health Config Manager Initialized (Simplified)")
        print(f"   Mode: ONLY API KEY from AWS, rest hardcoded")
        print(f"   Environment: {self.env}")
        print(f"   Region: {self.region_name}")
        print(f"   Application Code: {self.aplctn_cd}")
        print(f"   App ID: {self.app_id}")
        
        # Fetch ONLY API key from AWS if enabled
        if self.use_aws_secrets:
            if RRR_AVAILABLE:
                print(f"   AWS Secrets: ENABLED (fetching API key only)")
                self._fetch_api_key_from_aws()
            else:
                print("   ⚠️ RRR not available - API key must be set manually")
        else:
            print("   ℹ️ AWS disabled - API key must be set manually")
    
    def _fetch_api_key_from_aws(self):
        """
        Fetch ONLY the API key from AWS Secrets Manager using RRR library
        
        ⚠️ All other configurations remain hardcoded in HealthAnalysisConfig!
        
        AWS Secret Path: {env}/api/{aplctn_cd}
        Secret Key Name: api_key (or api-key or apikey)
        """
        try:
            print(f"\n🔐 Fetching API key from AWS Secrets Manager...")
            print(f"   Secret path: {self.env}/api/{self.aplctn_cd}")
            print(f"   App ID: {self.app_id}")
            
            # Prepare headers with placeholder for API key
            input_headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
                "api-key": "$${api_key}"  # ⚠️ Placeholder - RRR replaces with actual key
            }
            
            # Call RRR's get_api_secrets function
            params, headers, body, cert = get_api_secrets(
                log=self.logger,
                env=self.env,
                region_name=self.region_name,
                aplctn_cd=self.aplctn_cd,
                auth_type='api_key',
                provider='',  # Empty as requested
                app_id=self.app_id,
                params={},
                headers=input_headers,
                body={}
            )
            
            # Store headers and cert
            self.headers_with_secrets = headers
            self.config.cert_path = cert
            
            # Extract ONLY the API key from headers
            self.config.api_key = headers.get('api-key') or headers.get('apikey') or headers.get('api_key') or ""
            
            if self.config.api_key:
                print(f"   ✅ API key fetched successfully!")
                print(f"   ✅ Key length: {len(self.config.api_key)} characters")
            else:
                print(f"   ⚠️ WARNING: API key not found in AWS secrets!")
            
            if cert:
                print(f"   ✅ SSL cert: {cert}")
            else:
                print(f"   ℹ️ No SSL cert provided")
            
            print(f"✅ AWS API key fetch completed!\n")
            
        except Exception as e:
            print(f"\n❌ ERROR: Failed to fetch API key from AWS: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback
            self.headers_with_secrets = {
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json"
            }
            print(f"⚠️ Continuing with empty API key - must be set manually!\n")
    
    def set_api_key(self, api_key: str):
        """
        Manually set the API key (for local development or override)
        
        Args:
            api_key: Snowflake Cortex API key
        """
        self.config.api_key = api_key
        print(f"✅ API key set manually: {len(api_key)} characters")
    
    def update_config(self, **kwargs):
        """
        Update hardcoded configuration values (if needed)
        
        Args:
            **kwargs: Configuration parameters to update (e.g., fastapi_url, model, etc.)
        """
        print("\n🔄 Updating configuration...")
        
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                display_value = value if key != 'api_key' else f'[REDACTED - {len(value)} chars]'
                print(f"   ✅ Updated {key}: {display_value}")
            else:
                print(f"   ⚠️ Unknown config key: {key}")
        
        print("✅ Configuration updated")
    
    def get_config(self) -> HealthAnalysisConfig:
        """Get the current configuration"""
        return self.config
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            'fastapi_url': self.config.fastapi_url,
            'api_url': self.config.api_url,
            'api_key': self.config.api_key,
            'app_id': self.config.app_id,
            'aplctn_cd': self.config.aplctn_cd,
            'model': self.config.model,
            'sys_msg': self.config.sys_msg,
            'chatbot_sys_msg': self.config.chatbot_sys_msg,
            'timeout': self.config.timeout,
            'heart_attack_api_url': self.config.heart_attack_api_url,
            'heart_attack_threshold': self.config.heart_attack_threshold,
            'env': self.config.env,
            'region_name': self.config.region_name,
            'headers': self.headers_with_secrets,
            'cert_path': self.config.cert_path
        }
    
    def print_config_summary(self):
        """Print a summary of the current configuration"""
        print("\n" + "="*80)
        print("📋 HEALTH ANALYSIS AGENT CONFIGURATION")
        print("="*80)
        
        print("\n✅ HARDCODED CONFIGURATIONS:")
        print(f"   Snowflake API URL: {self.config.api_url}")
        print(f"   FastAPI/MCP Server: {self.config.fastapi_url}")
        print(f"   Heart Attack ML API: {self.config.heart_attack_api_url}")
        print(f"   Model: {self.config.model}")
        print(f"   App ID: {self.config.app_id}")
        print(f"   Application Code: {self.config.aplctn_cd}")
        print(f"   Timeout: {self.config.timeout}s")
        print(f"   Heart Attack Threshold: {self.config.heart_attack_threshold}")
        
        print("\n🔐 FROM AWS SECRETS MANAGER:")
        if self.config.api_key:
            print(f"   Snowflake API Key: ✅ [SET - {len(self.config.api_key)} chars]")
        else:
            print(f"   Snowflake API Key: ❌ [NOT SET]")
        
        if self.config.cert_path:
            print(f"   SSL Certificate: ✅ {self.config.cert_path}")
        else:
            print(f"   SSL Certificate: ℹ️ [NONE]")
        
        print("\n☁️ AWS CONFIGURATION:")
        print(f"   Environment: {self.config.env}")
        print(f"   Region: {self.config.region_name}")
        print(f"   Secret Path: {self.config.env}/api/{self.config.aplctn_cd}")
        
        print("\n" + "="*80 + "\n")
    
    def validate_config(self) -> bool:
        """Validate that required configuration is present"""
        print("\n🔍 Validating configuration...")
        
        is_valid = True
        
        # Check API key (the only thing from AWS)
        if not self.config.api_key or self.config.api_key == "":
            print("   ❌ CRITICAL: Snowflake API Key is missing!")
            print("      Must be fetched from AWS or set manually")
            is_valid = False
        else:
            print("   ✅ Valid: Snowflake API Key is set")
        
        # Check hardcoded values (should always be present)
        if not self.config.api_url:
            print("   ❌ Missing: API URL (hardcoded)")
            is_valid = False
        else:
            print("   ✅ Valid: API URL (hardcoded)")
        
        if is_valid:
            print(f"\n✅ Configuration validation PASSED")
        else:
            print(f"\n⚠️ Configuration validation FAILED")
        
        return is_valid


# ============================================================================
#                         HELPER FUNCTIONS
# ============================================================================

def create_health_config(env: str = "dev", region_name: str = "us-east-2",
                        aplctn_cd: str = "aedl", app_id: str = "edadip") -> HealthConfigManager:
    """
    Create Health Config Manager with AWS API key
    
    ⚠️ ONLY API KEY is fetched from AWS
    ✅ All other configs are hardcoded
    
    Args:
        env: AWS environment (dev, sit, prod)
        region_name: AWS region
        aplctn_cd: Application code
        app_id: Application ID
    
    Returns:
        HealthConfigManager with API key from AWS
    """
    return HealthConfigManager(
        env=env,
        region_name=region_name,
        aplctn_cd=aplctn_cd,
        app_id=app_id,
        use_aws_secrets=True
    )


def create_local_health_config(api_key: str = "") -> HealthConfigManager:
    """
    Create Health Config Manager for local development
    
    ⚠️ API key must be provided manually (not from AWS)
    ✅ All other configs are hardcoded
    
    Args:
        api_key: Snowflake API key (manual for local dev)
    
    Returns:
        HealthConfigManager with manual API key
    """
    config_manager = HealthConfigManager(use_aws_secrets=False)
    
    if api_key:
        config_manager.set_api_key(api_key)
    
    return config_manager


# ============================================================================
#                         USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("🏥 HEALTH CONFIG MANAGER - SIMPLIFIED VERSION")
    print("   ⚠️ ONLY API KEY from AWS, all else hardcoded ✅")
    print("="*80)
    
    print("\n📝 Example 1: Fetch API key from AWS (RECOMMENDED)")
    print("-" * 80)
    config_mgr = create_health_config(
        env="dev",
        region_name="us-east-2",
        aplctn_cd="aedl",
        app_id="edadip"
    )
    config_mgr.print_config_summary()
    config_mgr.validate_config()
    
    print("\n📝 Example 2: Local development with manual API key")
    print("-" * 80)
    local_config_mgr = create_local_health_config(
        api_key="your-manual-api-key-here"
    )
    local_config_mgr.print_config_summary()
    local_config_mgr.validate_config()
    
    print("\n📝 Example 3: Override hardcoded values (optional)")
    print("-" * 80)
    config_mgr.update_config(
        fastapi_url="http://custom-server:8080",
        model="different-model"
    )
    
    print("\n" + "="*80)
    print("✅ Examples completed!")
    print("   Remember: ONLY API key comes from AWS")
    print("   Everything else is hardcoded in HealthAnalysisConfig")
    print("="*80)
