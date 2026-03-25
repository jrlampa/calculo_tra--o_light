#!/usr/bin/env python3
"""
Script de validação do pipeline CI/CD.
Este script testa a integração completa do pipeline antes da implantação.
"""

import os
import sys
import asyncio
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any

# Configuração de logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineValidator:
    """Validador do pipeline CI/CD."""
    
    def __init__(self):
        self.validation_results = {}
        self.workflows_dir = Path('.github/workflows')
        self.python_dir = Path('python')
        
    def validate_workflow_files(self) -> Dict[str, Any]:
        """Valida a existência e estrutura dos arquivos de workflow."""
        results = {
            'ci.yml': False,
            'test-persistence.yml': False,
            'deploy.yml': False,
            'test-setup.yml': False,
            'total_workflows': 0
        }
        
        try:
            if self.workflows_dir.exists():
                workflow_files = list(self.workflows_dir.glob('*.yml'))
                results['total_workflows'] = len(workflow_files)
                
                for workflow_file in workflow_files:
                    if workflow_file.name in results:
                        results[workflow_file.name] = True
                        logger.info(f"✅ Found workflow: {workflow_file.name}")
                    else:
                        logger.info(f"ℹ️  Additional workflow: {workflow_file.name}")
                
                # Validar sintaxe YAML
                for workflow_file in workflow_files:
                    if not self._validate_yaml_syntax(workflow_file):
                        logger.error(f"❌ Invalid YAML syntax in {workflow_file.name}")
                        results[workflow_file.name] = False
                    else:
                        logger.info(f"✅ Valid YAML syntax in {workflow_file.name}")
                        
        except Exception as e:
            logger.error(f"Error validating workflow files: {e}")
        
        return results
    
    def _validate_yaml_syntax(self, file_path: Path) -> bool:
        """Valida a sintaxe YAML de um arquivo."""
        try:
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            return True
        except Exception:
            return False
    
    def validate_test_files(self) -> Dict[str, Any]:
        """Valida a existência dos arquivos de teste."""
        results = {
            'executar_testes_persistencia.py': False,
            'ci_cd_integration.py': False,
            'test_hierarquia_completa.py': False,
            'test_persistencia_calculo.py': False,
            'test_parity_excel.py': False,
            'test_integracao_real.py': False,
            'total_test_files': 0
        }
        
        try:
            if self.python_dir.exists():
                # Validar arquivos principais
                main_files = [
                    'executar_testes_persistencia.py',
                    'ci_cd_integration.py'
                ]
                
                for file_name in main_files:
                    file_path = self.python_dir / file_name
                    if file_path.exists():
                        results[file_name] = True
                        logger.info(f"✅ Found main file: {file_name}")
                
                # Validar arquivos de testes
                tests_dir = self.python_dir / 'tests'
                if tests_dir.exists():
                    test_files = list(tests_dir.glob('test_*.py'))
                    results['total_test_files'] = len(test_files)
                    
                    for test_file in test_files:
                        if test_file.name in results:
                            results[test_file.name] = True
                            logger.info(f"✅ Found test file: {test_file.name}")
                
        except Exception as e:
            logger.error(f"Error validating test files: {e}")
        
        return results
    
    def validate_dependencies(self) -> Dict[str, Any]:
        """Valida as dependências do projeto."""
        results = {
            'python_requirements': False,
            'node_package_json': False,
            'docker_files': False,
            'total_dependencies': 0
        }
        
        try:
            # Validar requirements.txt
            requirements_file = self.python_dir / 'requirements.txt'
            if requirements_file.exists():
                results['python_requirements'] = True
                results['total_dependencies'] += 1
                logger.info("✅ Found Python requirements.txt")
            
            # Validar package.json
            package_json = Path('package.json')
            if package_json.exists():
                results['node_package_json'] = True
                results['total_dependencies'] += 1
                logger.info("✅ Found Node.js package.json")
            
            # Validar Dockerfiles
            docker_files = [
                'Dockerfile.api',
                'Dockerfile.web'
            ]
            
            for docker_file in docker_files:
                if Path(docker_file).exists():
                    results['docker_files'] = True
                    results['total_dependencies'] += 1
                    logger.info(f"✅ Found Dockerfile: {docker_file}")
                    
        except Exception as e:
            logger.error(f"Error validating dependencies: {e}")
        
        return results
    
    def validate_environment_setup(self) -> Dict[str, Any]:
        """Valida a configuração do ambiente de testes."""
        results = {
            'environment_variables': [],
            'database_config': False,
            'supabase_config': False,
            'redis_config': False
        }
        
        try:
            # Verificar variáveis de ambiente críticas
            critical_vars = [
                'DATABASE_URL',
                'SUPABASE_URL', 
                'SUPABASE_KEY',
                'REDIS_URL'
            ]
            
            for var in critical_vars:
                value = os.getenv(var)
                if value:
                    results['environment_variables'].append(var)
                    logger.info(f"✅ Environment variable set: {var}")
                else:
                    logger.warning(f"⚠️  Environment variable not set: {var}")
            
            # Validar configuração de banco de dados
            if 'DATABASE_URL' in results['environment_variables']:
                results['database_config'] = True
            
            # Validar configuração do Supabase
            if 'SUPABASE_URL' in results['environment_variables'] and 'SUPABASE_KEY' in results['environment_variables']:
                results['supabase_config'] = True
            
            # Validar configuração do Redis
            if 'REDIS_URL' in results['environment_variables']:
                results['redis_config'] = True
                
        except Exception as e:
            logger.error(f"Error validating environment setup: {e}")
        
        return results
    
    async def validate_database_connection(self) -> Dict[str, Any]:
        """Valida a conexão com o banco de dados."""
        results = {
            'connection_test': False,
            'connection_details': {},
            'error_message': None
        }
        
        try:
            # Testar conexão com banco de dados
            from db.supabase_client import get_supabase_client
            
            client = get_supabase_client()
            result = await client.fetch_one('SELECT 1 as test')
            
            if result and result['test'] == 1:
                results['connection_test'] = True
                results['connection_details'] = {
                    'status': 'connected',
                    'test_query': 'SELECT 1',
                    'result': result
                }
                logger.info("✅ Database connection successful")
            else:
                results['error_message'] = "Database connection test failed"
                logger.error("❌ Database connection test failed")
                
        except Exception as e:
            results['error_message'] = str(e)
            logger.error(f"❌ Database connection error: {e}")
        
        return results
    
    def validate_test_execution(self) -> Dict[str, Any]:
        """Valida a execução dos testes."""
        results = {
            'pytest_available': False,
            'test_discovery': False,
            'test_execution': False,
            'test_files_found': []
        }
        
        try:
            # Verificar se pytest está disponível
            result = subprocess.run([
                sys.executable, '-c', 'import pytest; print(pytest.__version__)'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                results['pytest_available'] = True
                logger.info(f"✅ Pytest available: {result.stdout.strip()}")
            
            # Descobrir arquivos de teste
            tests_dir = self.python_dir / 'tests'
            if tests_dir.exists():
                test_files = list(tests_dir.glob('test_*.py'))
                results['test_files_found'] = [f.name for f in test_files]
                results['test_discovery'] = len(test_files) > 0
                
                if results['test_discovery']:
                    logger.info(f"✅ Found {len(test_files)} test files")
                    for test_file in test_files:
                        logger.info(f"  - {test_file.name}")
            
            # Testar execução de um teste simples
            if results['pytest_available'] and results['test_discovery']:
                result = subprocess.run([
                    sys.executable, '-m', 'pytest', '--collect-only', '-q'
                ], capture_output=True, text=True, cwd=self.python_dir)
                
                if result.returncode == 0:
                    results['test_execution'] = True
                    logger.info("✅ Test execution validation successful")
                else:
                    logger.error(f"❌ Test execution validation failed: {result.stderr}")
                    
        except Exception as e:
            logger.error(f"Error validating test execution: {e}")
        
        return results
    
    def generate_validation_report(self) -> str:
        """Gera um relatório de validação."""
        report = """
# Pipeline CI/CD Validation Report

## Summary
"""
        
        # Contar resultados positivos
        total_checks = 0
        passed_checks = 0
        
        for category, results in self.validation_results.items():
            if isinstance(results, dict):
                for key, value in results.items():
                    if key != 'error_message' and key != 'connection_details' and key != 'test_files_found':
                        total_checks += 1
                        if value is True or (isinstance(value, list) and len(value) > 0):
                            passed_checks += 1
        
        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        report += f"- **Total Checks**: {total_checks}\n"
        report += f"- **Passed**: {passed_checks}\n"
        report += f"- **Failed**: {total_checks - passed_checks}\n"
        report += f"- **Success Rate**: {success_rate:.1f}%\n\n"
        
        # Detalhes por categoria
        for category, results in self.validation_results.items():
            report += f"## {category.replace('_', ' ').title()}\n\n"
            
            if isinstance(results, dict):
                for key, value in results.items():
                    if key == 'error_message' and value:
                        report += f"- **{key}**: ❌ {value}\n"
                    elif key == 'connection_details' and value:
                        report += f"- **{key}**: ✅ {value}\n"
                    elif key == 'test_files_found' and value:
                        report += f"- **{key}**: ✅ {len(value)} files found\n"
                        for file_name in value:
                            report += f"  - {file_name}\n"
                    elif key == 'environment_variables' and value:
                        report += f"- **{key}**: ✅ {len(value)} variables set\n"
                        for var in value:
                            report += f"  - {var}\n"
                    elif isinstance(value, bool):
                        status = "✅" if value else "❌"
                        report += f"- **{key}**: {status}\n"
                    elif isinstance(value, int):
                        report += f"- **{key}**: {value}\n"
            
            report += "\n"
        
        # Recomendações
        report += "## Recommendations\n\n"
        
        if success_rate < 100:
            report += "### Critical Issues\n"
            if not self.validation_results.get('workflow_files', {}).get('ci.yml', False):
                report += "- ❌ Missing main CI workflow file\n"
            if not self.validation_results.get('test_files', {}).get('executar_testes_persistencia.py', False):
                report += "- ❌ Missing persistence test execution script\n"
            if not self.validation_results.get('dependencies', {}).get('python_requirements', False):
                report += "- ❌ Missing Python requirements file\n"
        
        report += "### Next Steps\n"
        report += "- Run the CI/CD pipeline to validate integration\n"
        report += "- Monitor test execution in GitHub Actions\n"
        report += "- Review and update documentation as needed\n"
        report += "- Set up monitoring and alerting for production\n\n"
        
        # Conclusão
        report += "## Conclusion\n\n"
        if success_rate == 100:
            report += "🎉 **Pipeline validation completed successfully!**\n"
            report += "The CI/CD pipeline is ready for production use.\n"
        else:
            report += "⚠️  **Pipeline validation has issues that need to be addressed.**\n"
            report += "Please review the failed checks and resolve them before deploying.\n"
        
        return report
    
    async def run_validation(self) -> bool:
        """Executa a validação completa do pipeline."""
        logger.info("🚀 Starting pipeline validation...")
        
        # 1. Validar arquivos de workflow
        logger.info("📋 Validating workflow files...")
        self.validation_results['workflow_files'] = self.validate_workflow_files()
        
        # 2. Validar arquivos de teste
        logger.info("🧪 Validating test files...")
        self.validation_results['test_files'] = self.validate_test_files()
        
        # 3. Validar dependências
        logger.info("📦 Validating dependencies...")
        self.validation_results['dependencies'] = self.validate_dependencies()
        
        # 4. Validar configuração de ambiente
        logger.info("⚙️  Validating environment setup...")
        self.validation_results['environment_setup'] = self.validate_environment_setup()
        
        # 5. Validar conexão com banco de dados
        logger.info("🗄️  Validating database connection...")
        self.validation_results['database_connection'] = await self.validate_database_connection()
        
        # 6. Validar execução de testes
        logger.info("🏃 Validating test execution...")
        self.validation_results['test_execution'] = self.validate_test_execution()
        
        # 7. Gerar relatório
        logger.info("📊 Generating validation report...")
        report = self.generate_validation_report()
        
        # Salvar relatório
        with open('pipeline_validation_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Determinar sucesso
        total_checks = 0
        passed_checks = 0
        
        for category, results in self.validation_results.items():
            if isinstance(results, dict):
                for key, value in results.items():
                    if key != 'error_message' and key != 'connection_details' and key != 'test_files_found':
                        total_checks += 1
                        if value is True or (isinstance(value, list) and len(value) > 0):
                            passed_checks += 1
        
        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        success = success_rate >= 80  # 80% de sucesso é aceitável
        
        logger.info(f"✅ Pipeline validation completed with {success_rate:.1f}% success rate")
        
        return success


async def main():
    """Função principal de validação."""
    validator = PipelineValidator()
    success = await validator.run_validation()
    
    # Exibir resumo
    print("\n" + "="*60)
    print("PIPELINE VALIDATION SUMMARY")
    print("="*60)
    
    workflow_files = validator.validation_results.get('workflow_files', {})
    test_files = validator.validation_results.get('test_files', {})
    dependencies = validator.validation_results.get('dependencies', {})
    
    print(f"Workflow Files: {'✅' if workflow_files.get('total_workflows', 0) >= 4 else '❌'}")
    print(f"Test Files: {'✅' if test_files.get('total_test_files', 0) >= 4 else '❌'}")
    print(f"Dependencies: {'✅' if dependencies.get('total_dependencies', 0) >= 3 else '❌'}")
    print(f"Overall Result: {'✅ SUCCESS' if success else '❌ FAILURE'}")
    
    print("\nDetailed report saved to: pipeline_validation_report.md")
    
    # Salvar resultados em JSON
    with open('pipeline_validation_results.json', 'w', encoding='utf-8') as f:
        json.dump(validator.validation_results, f, indent=2)
    
    print("Validation results saved to: pipeline_validation_results.json")
    
    # Exit com código apropriado
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())