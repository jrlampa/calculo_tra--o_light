#!/usr/bin/env python3
"""
Advanced Test Environment Setup Script for calculo_tração_light.
This script automates the complete setup of test environments with validation.
"""

import os
import sys
import asyncio
import subprocess
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('setup_test_environment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TestEnvironmentSetup:
    """Setup and validation of test environments."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config = self._load_config()
        self.environment_validated = False
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_file = self.project_root / "test_environment_config.yml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            return self._generate_default_config()
    
    def _generate_default_config(self) -> Dict[str, Any]:
        """Generate default configuration."""
        config = {
            "environments": {
                "test": {
                    "database_url": "postgresql://test_user:test_pass@localhost:5432/calculo_tracao_test",
                    "redis_url": "redis://localhost:6379/1",
                    "supabase_url": "https://test-project.supabase.co",
                    "supabase_key": "test-key",
                    "log_level": "DEBUG"
                },
                "staging": {
                    "database_url": "postgresql://staging_user:staging_pass@localhost:5432/calculo_tracao_staging",
                    "redis_url": "redis://localhost:6379/2",
                    "supabase_url": "https://staging-project.supabase.co",
                    "supabase_key": "staging-key",
                    "log_level": "INFO"
                }
            },
            "services": {
                "postgresql": {"port": 5432, "required": True},
                "redis": {"port": 6379, "required": True},
                "supabase": {"url": "https://supabase.co", "required": False}
            },
            "dependencies": {
                "python": ">=3.10",
                "node": ">=16",
                "docker": ">=20.0"
            }
        }
        
        # Save default config
        config_file = self.project_root / "test_environment_config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Generated default config: {config_file}")
        return config
    
    async def setup_environment(self, env_name: str = "test") -> bool:
        """Setup complete test environment."""
        logger.info(f"Setting up test environment: {env_name}")
        
        try:
            # 1. Validate prerequisites
            if not await self._validate_prerequisites():
                return False
            
            # 2. Setup services
            if not await self._setup_services():
                return False
            
            # 3. Setup database
            if not await self._setup_database(env_name):
                return False
            
            # 4. Setup application
            if not await self._setup_application(env_name):
                return False
            
            # 5. Run validation tests
            if not await self._run_validation_tests(env_name):
                return False
            
            # 6. Generate environment report
            await self._generate_environment_report(env_name)
            
            logger.info(f"✅ Test environment {env_name} setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Environment setup failed: {e}")
            return False
    
    async def _validate_prerequisites(self) -> bool:
        """Validate system prerequisites."""
        logger.info("Validating prerequisites...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 10):
            logger.error(f"Python version {python_version.major}.{python_version.minor} is too old. Required: >=3.10")
            return False
        
        logger.info(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Node.js version: {result.stdout.strip()}")
            else:
                logger.warning("⚠️ Node.js not found, some frontend tests may fail")
        except FileNotFoundError:
            logger.warning("⚠️ Node.js not found, some frontend tests may fail")
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Docker version: {result.stdout.strip()}")
            else:
                logger.warning("⚠️ Docker not found, containerized tests will fail")
        except FileNotFoundError:
            logger.warning("⚠️ Docker not found, containerized tests will fail")
        
        return True
    
    async def _setup_services(self) -> bool:
        """Setup required services."""
        logger.info("Setting up services...")
        
        services = self.config['services']
        
        for service_name, service_config in services.items():
            if not service_config.get('required', True):
                continue
            
            port = service_config['port']
            
            # Check if service is running
            if not await self._check_service_running(port):
                logger.warning(f"⚠️ Service {service_name} not running on port {port}")
                
                # Try to start service
                if service_name == 'postgresql':
                    await self._start_postgresql()
                elif service_name == 'redis':
                    await self._start_redis()
            else:
                logger.info(f"✅ Service {service_name} running on port {port}")
        
        return True
    
    async def _check_service_running(self, port: int) -> bool:
        """Check if service is running on port."""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result == 0
        except:
            return False
    
    async def _start_postgresql(self):
        """Start PostgreSQL service."""
        logger.info("Starting PostgreSQL...")
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'postgresql'], check=True)
            await asyncio.sleep(3)  # Wait for service to start
            logger.info("✅ PostgreSQL started")
        except subprocess.CalledProcessError:
            logger.error("❌ Failed to start PostgreSQL")
    
    async def _start_redis(self):
        """Start Redis service."""
        logger.info("Starting Redis...")
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'redis-server'], check=True)
            await asyncio.sleep(2)  # Wait for service to start
            logger.info("✅ Redis started")
        except subprocess.CalledProcessError:
            logger.error("❌ Failed to start Redis")
    
    async def _setup_database(self, env_name: str) -> bool:
        """Setup database for environment."""
        logger.info(f"Setting up database for {env_name}...")
        
        env_config = self.config['environments'][env_name]
        db_url = env_config['database_url']
        
        # Create database if it doesn't exist
        try:
            # Extract database name from URL
            db_name = db_url.split('/')[-1].split('?')[0]
            
            # Create database
            create_cmd = f"createdb {db_name}"
            result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Database {db_name} created")
            elif "already exists" in result.stderr:
                logger.info(f"✅ Database {db_name} already exists")
            else:
                logger.error(f"❌ Failed to create database: {result.stderr}")
                return False
            
            # Run migrations
            migrate_cmd = f"python -m alembic upgrade head"
            result = subprocess.run(migrate_cmd, shell=True, capture_output=True, text=True, cwd=self.project_root / "python")
            
            if result.returncode == 0:
                logger.info("✅ Database migrations completed")
            else:
                logger.error(f"❌ Database migrations failed: {result.stderr}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            return False
        
        return True
    
    async def _setup_application(self, env_name: str) -> bool:
        """Setup application for environment."""
        logger.info(f"Setting up application for {env_name}...")
        
        env_config = self.config['environments'][env_name]
        
        # Create .env file
        env_file = self.project_root / ".env"
        with open(env_file, 'w') as f:
            for key, value in env_config.items():
                f.write(f"{key.upper()}={value}\n")
        
        logger.info(f"✅ Environment file created: {env_file}")
        
        # Install Python dependencies
        try:
            requirements_file = self.project_root / "python" / "requirements.txt"
            if requirements_file.exists():
                install_cmd = f"pip install -r {requirements_file}"
                result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("✅ Python dependencies installed")
                else:
                    logger.error(f"❌ Failed to install Python dependencies: {result.stderr}")
                    return False
        except Exception as e:
            logger.error(f"❌ Dependency installation failed: {e}")
            return False
        
        # Install Node.js dependencies
        try:
            node_dir = self.project_root
            if (node_dir / "package.json").exists():
                install_cmd = "npm install"
                result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True, cwd=node_dir)
                
                if result.returncode == 0:
                    logger.info("✅ Node.js dependencies installed")
                else:
                    logger.warning(f"⚠️ Node.js dependencies installation failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"⚠️ Node.js setup failed: {e}")
        
        return True
    
    async def _run_validation_tests(self, env_name: str) -> bool:
        """Run validation tests for environment."""
        logger.info(f"Running validation tests for {env_name}...")
        
        # Run Python tests
        try:
            test_cmd = "python -m pytest tests/ -v --tb=short"
            result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True, cwd=self.project_root / "python")
            
            if result.returncode == 0:
                logger.info("✅ Python tests passed")
            else:
                logger.warning(f"⚠️ Python tests failed: {result.stdout}")
                # Don't fail setup for test failures, just warn
        except Exception as e:
            logger.warning(f"⚠️ Python tests execution failed: {e}")
        
        # Run frontend tests
        try:
            test_cmd = "npm test"
            result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("✅ Frontend tests passed")
            else:
                logger.warning(f"⚠️ Frontend tests failed: {result.stdout}")
        except Exception as e:
            logger.warning(f"⚠️ Frontend tests execution failed: {e}")
        
        return True
    
    async def _generate_environment_report(self, env_name: str):
        """Generate environment setup report."""
        report = {
            "environment": env_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "services": {},
            "database": {},
            "application": {},
            "recommendations": []
        }
        
        # Check services
        for service_name, service_config in self.config['services'].items():
            port = service_config['port']
            report["services"][service_name] = {
                "running": await self._check_service_running(port),
                "port": port,
                "required": service_config.get('required', True)
            }
        
        # Check database
        env_config = self.config['environments'][env_name]
        db_url = env_config['database_url']
        db_name = db_url.split('/')[-1].split('?')[0]
        
        try:
            # Test database connection
            test_cmd = f"psql {db_url} -c 'SELECT 1;'"
            result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
            report["database"] = {
                "name": db_name,
                "connected": result.returncode == 0,
                "url": db_url
            }
        except Exception as e:
            report["database"] = {
                "name": db_name,
                "connected": False,
                "error": str(e)
            }
        
        # Generate recommendations
        if not report["services"]["postgresql"]["running"]:
            report["recommendations"].append("Start PostgreSQL service: sudo systemctl start postgresql")
        
        if not report["services"]["redis"]["running"]:
            report["recommendations"].append("Start Redis service: sudo systemctl start redis-server")
        
        if not report["database"]["connected"]:
            report["recommendations"].append("Check database connection and credentials")
        
        # Save report
        report_file = self.project_root / f"test_environment_report_{env_name}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Environment report saved: {report_file}")
        
        # Print summary
        logger.info("Environment Setup Summary:")
        logger.info(f"Services running: {sum(1 for s in report['services'].values() if s['running'])}/{len(report['services'])}")
        logger.info(f"Database connected: {report['database']['connected']}")
        if report["recommendations"]:
            logger.info("Recommendations:")
            for rec in report["recommendations"]:
                logger.info(f"  - {rec}")


async def main():
    """Main function."""
    setup = TestEnvironmentSetup()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        env_name = sys.argv[1]
    else:
        env_name = "test"
    
    logger.info(f"Starting test environment setup for: {env_name}")
    
    success = await setup.setup_environment(env_name)
    
    if success:
        logger.info("🎉 Test environment setup completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Test environment setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())