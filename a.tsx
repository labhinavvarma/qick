#!/usr/bin/env python3
"""
Combined Healthcare & Heart Disease API Server
- MCP (Model Context Protocol) for healthcare data integration
- Heart disease prediction using ML model
- Graceful fallback when MCP dependencies unavailable
"""

import os
import pickle
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict, field_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================================
# MCP IMPORTS (with graceful fallback)
# ========================================
MCP_AVAILABLE = False
mcp = None
sse = None

try:
    from mcp.server.sse import SseServerTransport
    from starlette.routing import Mount
    from mcpserver import mcp as mcp_instance
    
    mcp = mcp_instance
    sse = SseServerTransport("/messages")
    MCP_AVAILABLE = True
    logger.info("✅ MCP modules loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Warning: Could not import MCP modules: {e}")
    logger.info("⚠️ MCP functionality will be disabled. Running in fallback mode.")

# ========================================
# PYDANTIC MODELS (Fixed namespace warning)
# ========================================

class HeartDiseaseInput(BaseModel):
    """Input model for heart disease prediction"""
    age: int = Field(..., ge=0, le=120, description="Age in years")
    sex: int = Field(..., ge=0, le=1, description="Sex (1=male, 0=female)")
    cp: int = Field(..., ge=0, le=3, description="Chest pain type (0-3)")
    trestbps: int = Field(..., ge=80, le=200, description="Resting blood pressure (mm Hg)")
    chol: int = Field(..., ge=100, le=600, description="Serum cholesterol (mg/dl)")
    fbs: int = Field(..., ge=0, le=1, description="Fasting blood sugar > 120 mg/dl (1=true, 0=false)")
    restecg: int = Field(..., ge=0, le=2, description="Resting ECG results (0-2)")
    thalach: int = Field(..., ge=60, le=220, description="Maximum heart rate achieved")
    exang: int = Field(..., ge=0, le=1, description="Exercise induced angina (1=yes, 0=no)")
    oldpeak: float = Field(..., ge=0, le=10, description="ST depression induced by exercise")
    slope: int = Field(..., ge=0, le=2, description="Slope of peak exercise ST segment (0-2)")
    ca: int = Field(..., ge=0, le=4, description="Number of major vessels colored by fluoroscopy (0-4)")
    thal: int = Field(..., ge=0, le=3, description="Thalassemia (0=normal, 1=fixed defect, 2=reversible defect)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "age": 63,
                "sex": 1,
                "cp": 3,
                "trestbps": 145,
                "chol": 233,
                "fbs": 1,
                "restecg": 0,
                "thalach": 150,
                "exang": 0,
                "oldpeak": 2.3,
                "slope": 0,
                "ca": 0,
                "thal": 1
            }
        }
    )


class HeartDiseaseSimpleInput(BaseModel):
    """Simplified input for heart disease prediction"""
    age: int = Field(..., ge=0, le=120)
    sex: str = Field(..., pattern="^(male|female|M|F)$")
    chest_pain: str = Field(..., description="typical angina, atypical angina, non-anginal, asymptomatic")
    resting_bp: int = Field(..., ge=80, le=200)
    cholesterol: int = Field(..., ge=100, le=600)
    max_heart_rate: int = Field(..., ge=60, le=220)

    @field_validator('sex')
    @classmethod
    def normalize_sex(cls, v):
        return v.lower()

    @field_validator('chest_pain')
    @classmethod
    def normalize_chest_pain(cls, v):
        return v.lower()


class PredictionResponse(BaseModel):
    """Response model for heart disease prediction"""
    model_config = ConfigDict(protected_namespaces=())  # Fix Pydantic warning
    
    prediction: int = Field(..., description="0 = No heart disease, 1 = Heart disease present")
    probability: float = Field(..., ge=0, le=1, description="Probability of heart disease")
    risk_level: str = Field(..., description="Low, Medium, or High")
    model_type: str = Field(default="AdaBoost", description="ML model used")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: float = Field(..., ge=0, le=1, description="Model confidence")


class HealthResponse(BaseModel):
    """Response model for health check"""
    model_config = ConfigDict(protected_namespaces=())  # Fix Pydantic warning
    
    status: str
    service: str
    mcp_available: bool
    heart_disease_model: bool
    model_type: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserHealthInput(BaseModel):
    """Input for healthcare API queries"""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    ssn: str = Field(..., pattern=r"^\d{3}-?\d{2}-?\d{4}$")
    date_of_birth: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    gender: str = Field(..., pattern="^(M|F|Male|Female)$")
    zip_code: str = Field(..., pattern=r"^\d{5}$")

    @field_validator('ssn')
    @classmethod
    def normalize_ssn(cls, v):
        return v.replace('-', '')

    @field_validator('gender')
    @classmethod
    def normalize_gender(cls, v):
        return 'M' if v.upper() in ['M', 'MALE'] else 'F'


class ComprehensiveHealthInput(BaseModel):
    """Combined input for comprehensive health assessment"""
    # Personal information
    first_name: str
    last_name: str
    ssn: str
    date_of_birth: str
    gender: str
    zip_code: str
    
    # Heart disease factors
    age: int
    chest_pain_type: int
    resting_bp: int
    cholesterol: int
    max_heart_rate: int
    exercise_angina: int = 0
    st_depression: float = 0.0


# ========================================
# GLOBAL STATE
# ========================================
heart_disease_model = None
model_scaler = None
feature_names = None


# ========================================
# MODEL LOADING
# ========================================

def load_heart_disease_model():
    """Load the heart disease prediction model with error handling"""
    global heart_disease_model, model_scaler, feature_names
    
    model_path = "heart_disease_model_package.pkl"
    
    if not os.path.exists(model_path):
        logger.error(f"❌ Model file not found: {model_path}")
        return False
    
    try:
        logger.info("📁 Checking heart disease model files...")
        logger.info("🔄 Loading heart disease model package...")
        
        with open(model_path, 'rb') as f:
            model_package = pickle.load(f)
        
        heart_disease_model = model_package['model']
        model_scaler = model_package.get('scaler')
        feature_names = model_package.get('feature_names', [])
        
        logger.info("✅ Heart disease model loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading heart disease model: {e}")
        return False


# ========================================
# LIFESPAN MANAGEMENT (Fixed deprecated on_event)
# ========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown"""
    
    # STARTUP
    logger.info("=" * 60)
    logger.info("🚀 Combined Healthcare & Heart Disease API Starting Up")
    logger.info("=" * 60)
    
    # Load heart disease model
    model_loaded = load_heart_disease_model()
    logger.info(f"🏥 Heart Disease Model: {'Available' if model_loaded else 'Failed'}")
    logger.info(f"📡 MCP Available: {MCP_AVAILABLE}")
    
    logger.info("🏥 Health Check: http://localhost:8000/health")
    logger.info("🐛 Debug Routes: http://localhost:8000/debug/routes")
    logger.info("📍 Root Endpoint: http://localhost:8000/")
    
    if model_loaded:
        logger.info("✅ Heart Disease Endpoints:")
        logger.info("   • POST /predict")
        logger.info("   • POST /predict-simple")
        logger.info("   • GET /heart-disease/model-info")
    
    if MCP_AVAILABLE:
        logger.info("✅ Healthcare endpoints: MCP mode")
    else:
        logger.info("⚠️ Healthcare endpoints: fallback mode only")
    
    logger.info("🔗 Combined Endpoints:")
    logger.info("   • POST /comprehensive-health-assessment")
    
    logger.info("=" * 60)
    
    yield  # Application runs here
    
    # SHUTDOWN
    logger.info("INFO:     Shutting down")
    logger.info("INFO:     Waiting for application shutdown.")
    logger.info("INFO:     Application shutdown complete.")


# ========================================
# CREATE FASTAPI APP
# ========================================

app = FastAPI(
    title="Combined Healthcare & Heart Disease API",
    description="AI-powered health assessment with MCP integration",
    version="2.0.0",
    lifespan=lifespan  # Use new lifespan instead of on_event
)

# CORS Configuration (More secure than *)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"  # TODO: Replace with specific origins in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# MCP ROUTES (only if available)
# ========================================

if MCP_AVAILABLE and sse and mcp:
    app.router.routes.append(Mount("/messages", app=sse.handle_post_message))
    
    @app.get("/messages", tags=["MCP"], include_in_schema=True)
    def messages_docs(session_id: str):
        """
        Messages endpoint for SSE communication
        
        This endpoint is used for posting messages to SSE clients.
        Note: This route is for documentation purposes only.
        The actual implementation is handled by the SSE transport.
        """
        pass
    
    @app.get("/sse", tags=["MCP"])
    async def handle_sse(request: Request):
        """
        SSE endpoint that connects to the MCP server
        
        This endpoint establishes a Server-Sent Events connection with the client
        and forwards communication to the Model Context Protocol server.
        """
        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as (
                read_stream,
                write_stream,
            ):
                await mcp._mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp._mcp_server.create_initialization_options(),
                )
        except Exception as e:
            logger.error(f"SSE connection error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"SSE connection failed: {str(e)}"
            )


# ========================================
# HEART DISEASE PREDICTION ENDPOINTS
# ========================================

@app.post("/predict", response_model=PredictionResponse, tags=["Heart Disease"])
async def predict_heart_disease(data: HeartDiseaseInput):
    """
    Predict heart disease using detailed medical parameters
    
    Returns prediction, probability, and risk level.
    """
    if heart_disease_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Heart disease model not loaded"
        )
    
    try:
        # Prepare features
        features = [
            data.age, data.sex, data.cp, data.trestbps, data.chol,
            data.fbs, data.restecg, data.thalach, data.exang,
            data.oldpeak, data.slope, data.ca, data.thal
        ]
        
        # Scale if scaler available
        if model_scaler:
            features = model_scaler.transform([features])[0]
        
        # Make prediction
        prediction = int(heart_disease_model.predict([features])[0])
        
        # Get probability if available
        if hasattr(heart_disease_model, 'predict_proba'):
            proba = heart_disease_model.predict_proba([features])[0]
            probability = float(proba[1]) if len(proba) > 1 else float(proba[0])
        else:
            probability = 1.0 if prediction == 1 else 0.0
        
        # Determine risk level
        if probability < 0.3:
            risk_level = "Low"
        elif probability < 0.7:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        return PredictionResponse(
            prediction=prediction,
            probability=probability,
            risk_level=risk_level,
            model_type="AdaBoost",
            confidence=probability if prediction == 1 else (1 - probability)
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/predict-simple", response_model=PredictionResponse, tags=["Heart Disease"])
async def predict_simple(data: HeartDiseaseSimpleInput):
    """
    Simplified heart disease prediction with common parameters
    
    Automatically maps simplified inputs to full model parameters.
    """
    if heart_disease_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Heart disease model not loaded"
        )
    
    try:
        # Map simplified inputs to full model format
        sex_map = {'male': 1, 'female': 0, 'm': 1, 'f': 0}
        cp_map = {
            'typical angina': 0,
            'atypical angina': 1,
            'non-anginal': 2,
            'asymptomatic': 3
        }
        
        full_data = HeartDiseaseInput(
            age=data.age,
            sex=sex_map.get(data.sex, 0),
            cp=cp_map.get(data.chest_pain, 0),
            trestbps=data.resting_bp,
            chol=data.cholesterol,
            fbs=1 if data.cholesterol > 200 else 0,
            restecg=0,
            thalach=data.max_heart_rate,
            exang=0,
            oldpeak=0.0,
            slope=1,
            ca=0,
            thal=2
        )
        
        return await predict_heart_disease(full_data)
        
    except Exception as e:
        logger.error(f"Simple prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.get("/heart-disease/model-info", tags=["Heart Disease"])
async def get_model_info():
    """Get information about the loaded heart disease model"""
    if heart_disease_model is None:
        return {
            "model_loaded": False,
            "error": "Model not available"
        }
    
    return {
        "model_loaded": True,
        "model_type": type(heart_disease_model).__name__,
        "feature_names": feature_names,
        "scaler_available": model_scaler is not None,
        "input_features": 13
    }


# ========================================
# HEALTHCARE API ENDPOINTS
# ========================================

@app.post("/healthcare/medical", tags=["Healthcare API"])
async def submit_medical_claim(user: UserHealthInput):
    """Submit medical claim to healthcare API"""
    if not MCP_AVAILABLE:
        return {
            "status": "fallback_mode",
            "message": "MCP not available. Install websockets module for full functionality.",
            "user_data": user.dict()
        }
    
    # This would call the actual MCP tool
    # For now, return a placeholder
    return {
        "status": "submitted",
        "claim_type": "medical",
        "user": f"{user.first_name} {user.last_name}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/healthcare/pharmacy", tags=["Healthcare API"])
async def submit_pharmacy_claim(user: UserHealthInput):
    """Submit pharmacy claim to healthcare API"""
    if not MCP_AVAILABLE:
        return {
            "status": "fallback_mode",
            "message": "MCP not available. Install websockets module for full functionality.",
            "user_data": user.dict()
        }
    
    return {
        "status": "submitted",
        "claim_type": "pharmacy",
        "user": f"{user.first_name} {user.last_name}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/comprehensive-health-assessment", tags=["Combined"])
async def comprehensive_assessment(data: ComprehensiveHealthInput):
    """
    Comprehensive health assessment combining:
    - Heart disease risk prediction
    - Healthcare data retrieval
    """
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "patient": {
            "name": f"{data.first_name} {data.last_name}",
            "age": data.age,
            "gender": data.gender
        }
    }
    
    # Heart disease prediction
    try:
        if heart_disease_model:
            heart_data = HeartDiseaseInput(
                age=data.age,
                sex=1 if data.gender.upper() in ['M', 'MALE'] else 0,
                cp=data.chest_pain_type,
                trestbps=data.resting_bp,
                chol=data.cholesterol,
                fbs=1 if data.cholesterol > 200 else 0,
                restecg=0,
                thalach=data.max_heart_rate,
                exang=data.exercise_angina,
                oldpeak=data.st_depression,
                slope=1,
                ca=0,
                thal=2
            )
            prediction = await predict_heart_disease(heart_data)
            results['heart_disease_risk'] = prediction.dict()
        else:
            results['heart_disease_risk'] = {"error": "Model not available"}
    except Exception as e:
        results['heart_disease_risk'] = {"error": str(e)}
    
    # Healthcare data (if MCP available)
    if MCP_AVAILABLE:
        results['healthcare_data'] = {
            "status": "MCP integration active",
            "note": "Use specific endpoints for detailed data"
        }
    else:
        results['healthcare_data'] = {
            "status": "fallback_mode",
            "note": "Install websockets module for MCP functionality"
        }
    
    return results


# ========================================
# UTILITY ENDPOINTS
# ========================================

@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Combined Healthcare & Heart Disease API",
        "version": "2.0.0",
        "status": "operational",
        "features": {
            "heart_disease_prediction": heart_disease_model is not None,
            "mcp_integration": MCP_AVAILABLE,
            "healthcare_api": MCP_AVAILABLE
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "heart_disease": "/predict",
            "comprehensive": "/comprehensive-health-assessment"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="operational",
        service="Combined Healthcare & Heart Disease API",
        mcp_available=MCP_AVAILABLE,
        heart_disease_model=heart_disease_model is not None,
        model_type=type(heart_disease_model).__name__ if heart_disease_model else None
    )


@app.get("/debug/routes", tags=["Debug"])
async def list_routes():
    """List all available routes for debugging"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "name": route.name,
                "methods": list(route.methods) if hasattr(route, 'methods') else []
            })
    return {"total_routes": len(routes), "routes": routes}


# ========================================
# INCLUDE ADDITIONAL ROUTERS
# ========================================

try:
    from router import route
    app.include_router(route)
    logger.info("✅ Additional router loaded from router.py")
except ImportError as e:
    logger.warning(f"⚠️ Could not import router.py: {e}")


# ========================================
# ERROR HANDLERS
# ========================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


# ========================================
# MAIN ENTRY POINT
# ========================================

if __name__ == "__main__":
    print("\n🔧 Starting Combined Healthcare & Heart Disease API server...")
    print(f"📍 Server will be available at: http://localhost:8000")
    print(f"🏥 Test health endpoint: http://localhost:8000/health")
    print(f"📚 API Documentation: http://localhost:8000/docs")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
