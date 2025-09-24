"""
Configuration management for Shiny BPMS app
Migrated from Streamlit configuration loading
"""

import yaml
import json
import duckdb
from typing import Dict, Any, Tuple
from pathlib import Path

class ConfigManager:
    """Centralized configuration management for the BPMS application"""
    
    def __init__(self):
        self.workflow_config = {}
        self.form_config = {}
        self.form_data = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all configuration files"""
        try:
            self.workflow_config = self._load_yaml('workflow.yaml')
            self.form_config = self._load_yaml('form.yaml')
            self.form_data = self._load_json('data.json')
        except Exception as e:
            print(f"Warning: Error loading configurations: {e}")
            self._set_defaults()
    
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            with open(filename, 'r') as f:
                return yaml.safe_load(f.read())
        except FileNotFoundError:
            print(f"Warning: {filename} not found")
            return {}
        except yaml.YAMLError as e:
            print(f"Warning: Error parsing {filename}: {e}")
            return {}
    
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON data file"""
        try:
            with open(filename, 'r') as f:
                return json.loads(f.read())
        except FileNotFoundError:
            print(f"Warning: {filename} not found")
            return {}
        except json.JSONDecodeError as e:
            print(f"Warning: Error parsing {filename}: {e}")
            return {}
    
    def _set_defaults(self):
        """Set default configurations if files are missing"""
        self.workflow_config = {
            'workflow': {
                'start': {
                    'class': 'Start',
                    'id': 1,
                    'require_user_action': False
                }
            }
        }
        
        self.form_config = {
            'form': {
                'fields': {},
                'actions': {},
                'permissions': {}
            }
        }
        
        self.form_data = {
            'status': '',
            'user': 'GENERAL_USER'
        }
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """Get workflow configuration"""
        return self.workflow_config
    
    def get_form_config(self) -> Dict[str, Any]:
        """Get form configuration"""
        return self.form_config
    
    def get_form_data(self) -> Dict[str, Any]:
        """Get initial form data"""
        return self.form_data.copy()
    
    def reload_configs(self):
        """Reload all configurations from files"""
        self._load_all_configs()

class DatabaseManager:
    """Database connection and query management"""
    
    def __init__(self, db_path: str = 'bpms.db'):
        self.db_path = db_path
    
    def get_connection(self, read_only: bool = True):
        """Get DuckDB connection"""
        return duckdb.connect(self.db_path, read_only=read_only)
    
    def execute_query(self, query: str):
        """Execute SQL query and return DataFrame - raises exceptions for proper error handling"""
        # Security: Reject multi-statement queries
        # Allow single trailing semicolon but reject multiple statements
        query_clean = query.strip()
        if query_clean.endswith(';'):
            query_clean = query_clean[:-1].strip()
        
        # Check for remaining semicolons (indicates multiple statements)
        if ';' in query_clean:
            raise ValueError("Multi-statement queries are not allowed for security reasons")
            
        con = self.get_connection(read_only=True)
        try:
            result = con.sql(query).df()
            return result
        finally:
            con.close()
    
    def get_users(self):
        """Get users from database"""
        try:
            return self.execute_query("SELECT * FROM users LIMIT 100")
        except Exception:
            # Return empty DataFrame with helpful column names for missing table
            import pandas as pd
            return pd.DataFrame(columns=['user_id', 'username', 'email'])
    
    def get_roles(self):
        """Get roles from database"""
        try:
            return self.execute_query("SELECT * FROM roles LIMIT 100")
        except Exception:
            # Return empty DataFrame with helpful column names for missing table
            import pandas as pd
            return pd.DataFrame(columns=['role_id', 'role_name', 'description'])
    
    def get_permissions(self):
        """Get permissions from database"""
        try:
            return self.execute_query("SELECT * FROM permissions LIMIT 100")
        except Exception:
            # Return empty DataFrame with helpful column names for missing table
            import pandas as pd
            return pd.DataFrame(columns=['permission_id', 'permission_name', 'description'])

# Global instances
config_manager = ConfigManager()
db_manager = DatabaseManager()