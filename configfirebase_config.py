"""
Firebase configuration and client initialization.
Handles authentication and provides centralized Firestore/Realtime DB clients.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import firebase_admin
from firebase_admin import credentials, firestore, db
from google.cloud.firestore_v1.client import Client as FirestoreClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class FirebaseConfig:
    """Firebase configuration dataclass with validation"""
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    token_uri: str = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url: str = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url: str = ""


class FirebaseClient:
    """Singleton Firebase client with error handling and reconnection logic"""
    
    _instance: Optional['FirebaseClient'] = None
    _firestore_client: Optional[FirestoreClient] = None
    _realtime_db = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_from_env()
            self._initialized = True
    
    def _initialize_from_env(self) -> None:
        """Initialize Firebase from environment variables"""
        try:
            # Load credentials from environment
            config_dict = {
                "type": "service_account",
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL", "")
            }
            
            # Validate required fields
            required_fields = ["project_id", "private_key_id", "private_key", "client_email"]
            for field in required_fields:
                if not config_dict.get(field):
                    raise ValueError(f"Missing required Firebase config: {field}")
            
            # Initialize Firebase app
            if not firebase_admin._apps:
                cred = credentials.Certificate(config_dict)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': f"https://{config_dict['project_id']}-default-rtdb.firebaseio.com/"
                })
                logger.info(f"Firebase initialized for project: {config_dict['project_id']}")
            
            # Initialize clients
            self._firestore_client = firestore.client()
            self._realtime_db = db.reference()
            
            # Test connection
            self._test_connection()
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise
    
    def _test_connection(self) -> None:
        """Test Firebase connection by writing/reading a test document"""
        try:
            test_ref = self._firestore_client.collection('connection_tests').document('test')
            test_ref.set({'timestamp': firestore.SERVER_TIMESTAMP})
            test_ref.delete()
            logger.info("Firebase connection test successful")
        except Exception as e:
            logger.error(f"Firebase connection test failed: {str(e)}")
            raise
    
    @property
    def firestore(self) -> FirestoreClient:
        """Get Firestore client with lazy initialization"""
        if self._firestore_client is None:
            self._initialize_from_env()
        return self._firestore_client
    
    @property
    def realtime_db(self):
        """Get Realtime Database client with lazy initialization"""
        if self._realtime_db is None:
            self._initialize_from_env()
        return self._realtime_db
    
    def get_collection(self, collection_path: str):
        """Get Firestore collection with error handling"""
        try:
            return self.firestore.collection(collection_path)
        except Exception as e:
            logger.error(f"Failed to get collection {collection_path}: {str(e)}")
            raise
    
    def get_realtime_ref(self, path: str):
        """Get Realtime Database reference with error handling"""
        try:
            return self.realtime_db.child(path)
        except Exception as e:
            logger.error(f"Failed to get realtime ref {path}: {str(e)}")
            raise


# Global singleton instance
firebase_client = FirebaseClient()