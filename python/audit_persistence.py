"""
Comprehensive persistence audit for Cálculo Tração Light project.
Analyzes database structure, data integrity, and consistency WITHOUT FIXING anything.
"""

import asyncio
import os
import sys
from datetime import UTC, datetime
from typing import Dict, List, Any
from dotenv import load_dotenv
import json

# Add python to path
sys.path.append(os.path.join(os.getcwd(), "python"))

from db.pool import initialize_db_pool, db_pool


class PersistenceAudit:
    """Complete audit suite for persistence layer."""
    
    def __init__(self):
        self.findings: Dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "sections": {}
        }
        self.connection = None
    
    async def connect(self):
        """Initialize database connection."""
        await initialize_db_pool()
        self.connection = db_pool
        print("✓ Database pool initialized")
    
    async def audit_schema_structure(self):
        """Section 1: Audit database schema structure and completeness."""
        print("\n" + "="*80)
        print("1. SCHEMA STRUCTURE AUDIT")
        print("="*80)
        
        findings = {
            "tables": {},
            "indexes": [],
            "constraints": [],
            "warnings": []
        }
        
        try:
            # Get all tables
            tables_result = await self.connection.fetch_all("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            
            print(f"\n📋 Found {len(tables_result)} tables:")
            
            for table_row in tables_result:
                table_name = table_row['table_name']
                
                # Get columns for each table
                cols_result = await self.connection.fetch_all(f"""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_name = $1
                    ORDER BY ordinal_position
                """, table_name)
                
                table_info = {
                    "column_count": len(cols_result),
                    "columns": []
                }
                
                for col in cols_result:
                    table_info["columns"].append({
                        "name": col['column_name'],
                        "type": col['data_type'],
                        "nullable": col['is_nullable'],
                        "default": col['column_default'] is not None
                    })
                
                findings["tables"][table_name] = table_info
                print(f"  • {table_name} ({len(cols_result)} cols)")
            
            # Get indexes
            indexes_result = await self.connection.fetch_all("""
                SELECT 
                    tablename, 
                    indexname, 
                    indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
            
            print(f"\n📑 Found {len(indexes_result)} indexes:")
            for idx in indexes_result:
                findings["indexes"].append({
                    "table": idx['tablename'],
                    "name": idx['indexname'],
                    "definition": idx['indexdef']
                })
                print(f"  • {idx['indexname']} on {idx['tablename']}")
            
            # Get constraints
            constraints_result = await self.connection.fetch_all("""
                SELECT 
                    table_name,
                    constraint_name,
                    constraint_type
                FROM information_schema.table_constraints
                WHERE table_schema = 'public'
                ORDER BY table_name, constraint_name
            """)
            
            print(f"\n🔐 Found {len(constraints_result)} constraints:")
            for const in constraints_result:
                findings["constraints"].append({
                    "table": const['table_name'],
                    "name": const['constraint_name'],
                    "type": const['constraint_type']
                })
                print(f"  • {const['constraint_name']} ({const['constraint_type']}) on {const['table_name']}")
            
            # Check for expected tables
            expected_tables = ['projetos', 'pontos', 'niveis_calculo', 'travessias', 'cabos', 'postes', 'redes']
            actual_tables = [t['table_name'] for t in tables_result]
            missing_tables = [t for t in expected_tables if t not in actual_tables]
            
            if missing_tables:
                msg = f"⚠️  Missing {len(missing_tables)} expected tables: {', '.join(missing_tables)}"
                findings["warnings"].append(msg)
                print(f"\n{msg}")
            else:
                print(f"\n✅ All {len(expected_tables)} expected tables present")
        
        except Exception as e:
            findings["error"] = str(e)
            print(f"❌ Schema audit error: {e}")
        
        self.findings["sections"]["schema_structure"] = findings
        return findings
    
    async def audit_data_volume(self):
        """Section 2: Audit data volume and distribution."""
        print("\n" + "="*80)
        print("2. DATA VOLUME AUDIT")
        print("="*80)
        
        findings = {
            "table_sizes": {},
            "largest_tables": [],
            "empty_tables": [],
            "warnings": []
        }
        
        try:
            # Get row counts
            tables_result = await self.connection.fetch_all("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            print("\n📊 Record counts by table:\n")
            
            for table_row in tables_result:
                table_name = table_row['table_name']
                count_result = await self.connection.fetch_one(f"SELECT COUNT(*) as cnt FROM {table_name}")
                count = count_result['cnt']
                
                findings["table_sizes"][table_name] = count
                
                if count == 0:
                    findings["empty_tables"].append(table_name)
                    print(f"  ⚫ {table_name:30} {count:10,} rows [EMPTY]")
                else:
                    print(f"  ✓ {table_name:30} {count:10,} rows")
            
            # Sort by largest
            findings["largest_tables"] = sorted(
                findings["table_sizes"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Check for data issues
            if len(findings["empty_tables"]) > 0:
                msg = f"⚠️  {len(findings['empty_tables'])} empty tables: {', '.join(findings['empty_tables'])}"
                findings["warnings"].append(msg)
                print(f"\n{msg}")
            
            # If projetos exists and has data, audit pontos per projeto
            if 'projetos' in findings["table_sizes"] and findings["table_sizes"]['projetos'] > 0:
                proj_stats = await self.connection.fetch_all("""
                    SELECT 
                        p.id, p.nome, COUNT(pt.id) as pontos_count
                    FROM projetos p
                    LEFT JOIN pontos pt ON p.id = pt.projeto_id
                    GROUP BY p.id, p.nome
                    ORDER BY pontos_count DESC
                """)
                
                print(f"\n📈 Projetos and their points:\n")
                for proj in proj_stats:
                    print(f"  • {proj['nome']:40} {proj['pontos_count']:3} pontos")
        
        except Exception as e:
            findings["error"] = str(e)
            print(f"❌ Data volume audit error: {e}")
        
        self.findings["sections"]["data_volume"] = findings
        return findings
    
    async def audit_referential_integrity(self):
        """Section 3: Audit foreign key relationships and orphan records."""
        print("\n" + "="*80)
        print("3. REFERENTIAL INTEGRITY AUDIT")
        print("="*80)
        
        findings = {
            "orphan_records": {},
            "relationship_health": {},
            "warnings": []
        }
        
        try:
            # Check foreign keys
            fk_result = await self.connection.fetch_all("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                ORDER BY tc.table_name, tc.constraint_name
            """)
            
            print(f"\n🔗 Foreign Key Relationships ({len(fk_result)}):\n")
            
            for fk in fk_result:
                relation = f"{fk['table_name']}.{fk['column_name']} → {fk['foreign_table_name']}.{fk['foreign_column_name']}"
                print(f"  • {relation}")
                
                # Check for orphans in this relationship
                if fk['table_name'] == 'pontos' and fk['foreign_table_name'] == 'projetos':
                    orphan_result = await self.connection.fetch_all(f"""
                        SELECT COUNT(*) as orphan_count
                        FROM {fk['table_name']} child
                        LEFT JOIN {fk['foreign_table_name']} parent 
                            ON child.{fk['column_name']} = parent.{fk['foreign_column_name']}
                        WHERE parent.{fk['foreign_column_name']} IS NULL
                            AND child.{fk['column_name']} IS NOT NULL
                    """)
                    
                    orphan_count = orphan_result[0]['orphan_count']
                    if orphan_count > 0:
                        findings["orphan_records"][relation] = orphan_count
                        msg = f"⚠️  Found {orphan_count} orphans in {relation}"
                        findings["warnings"].append(msg)
                        print(f"    {msg}")
                    else:
                        print(f"    ✓ No orphans")
            
            # Check referential integrity for main flow: projetos → pontos → niveis_calculo → travessias
            if 'projetos' in await self._get_table_names():
                valid_projetos = await self.connection.fetch_one("""
                    SELECT COUNT(*) as cnt FROM projetos
                """)
                print(f"\n✓ Projetos: {valid_projetos['cnt']}")
                
                valid_pontos = await self.connection.fetch_all("""
                    SELECT p.nome, COUNT(pt.id) as pontos_count
                    FROM projetos p
                    LEFT JOIN pontos pt ON p.id = pt.projeto_id
                    GROUP BY p.id, p.nome
                    HAVING COUNT(pt.id) > 0
                """)
                print(f"✓ Pontos with parent projetos: {len(valid_pontos)}")
                
                findings["relationship_health"]["projeto_pontos_coverage"] = len(valid_pontos)
        
        except Exception as e:
            findings["error"] = str(e)
            print(f"❌ Referential integrity error: {e}")
        
        self.findings["sections"]["referential_integrity"] = findings
        return findings
    
    async def audit_data_completeness(self):
        """Section 4: Audit completeness of required fields."""
        print("\n" + "="*80)
        print("4. DATA COMPLETENESS AUDIT")
        print("="*80)
        
        findings = {
            "null_analysis": {},
            "field_coverage": {},
            "warnings": []
        }
        
        try:
            # Check nullability in key tables
            key_tables = {
                "projetos": ["nome", "orgao", "estudado_por", "criado_em"],
                "pontos": ["ponto", "projeto_id", "criado_em"],
                "niveis_calculo": ["ponto_id", "nivel"],
                "travessias": ["nivel_id", "posicao"]
            }
            
            print("\n🎯 Null value analysis in key tables:\n")
            
            for table_name, required_cols in key_tables.items():
                table_exists = await self._table_exists(table_name)
                if not table_exists:
                    print(f"  ⚫ {table_name} [NOT FOUND]")
                    continue
                
                findings["null_analysis"][table_name] = {}
                print(f"  {table_name}:")
                
                for col in required_cols:
                    col_exists = await self._column_exists(table_name, col)
                    if not col_exists:
                        print(f"    • {col:25} [COLUMN NOT FOUND]")
                        continue
                    
                    null_result = await self.connection.fetch_one(f"""
                        SELECT COUNT(*) as null_count FROM {table_name}
                        WHERE {col} IS NULL
                    """)
                    
                    total_result = await self.connection.fetch_one(f"""
                        SELECT COUNT(*) as total_count FROM {table_name}
                    """)
                    
                    null_count = null_result['null_count']
                    total_count = total_result['total_count']
                    
                    findings["null_analysis"][table_name][col] = {
                        "null_count": null_count,
                        "total_count": total_count,
                        "coverage_pct": 0 if total_count == 0 else round((total_count - null_count) / total_count * 100, 2)
                    }
                    
                    coverage = findings["null_analysis"][table_name][col]["coverage_pct"]
                    if null_count > 0:
                        msg = f"    ⚠️  {col:25} {coverage:5.1f}% coverage ({null_count} nulls)"
                        findings["warnings"].append(msg)
                        print(f"    {msg}")
                    else:
                        print(f"    ✓ {col:25} 100% coverage")
        
        except Exception as e:
            findings["error"] = str(e)
            print(f"❌ Data completeness error: {e}")
        
        self.findings["sections"]["data_completeness"] = findings
        return findings
    
    async def audit_timestamp_consistency(self):
        """Section 5: Audit timestamp fields for consistency."""
        print("\n" + "="*80)
        print("5. TIMESTAMP CONSISTENCY AUDIT")
        print("="*80)
        
        findings = {
            "timestamp_analysis": {},
            "warnings": []
        }
        
        try:
            # Check timestamp fields in main tables
            timestamp_tables = {
                "projetos": ["criado_em", "atualizado_em"],
                "pontos": ["criado_em", "atualizado_em"],
                "niveis_calculo": ["criado_em", "atualizado_em"],
                "travessias": ["criado_em", "atualizado_em"]
            }
            
            print("\n⏰ Timestamp field analysis:\n")
            
            for table_name, timestamp_cols in timestamp_tables.items():
                table_exists = await self._table_exists(table_name)
                if not table_exists:
                    continue
                
                findings["timestamp_analysis"][table_name] = {}
                print(f"  {table_name}:")
                
                for ts_col in timestamp_cols:
                    col_exists = await self._column_exists(table_name, ts_col)
                    if not col_exists:
                        continue
                    
                    ts_result = await self.connection.fetch_one(f"""
                        SELECT 
                            COUNT(*) as total_count,
                            COUNT({ts_col}) as non_null_count,
                            MIN({ts_col}) as min_ts,
                            MAX({ts_col}) as max_ts
                        FROM {table_name}
                    """)
                    
                    total = ts_result['total_count']
                    non_null = ts_result['non_null_count']
                    coverage = 0 if total == 0 else round(non_null / total * 100, 2)
                    
                    findings["timestamp_analysis"][table_name][ts_col] = {
                        "total": total,
                        "populated": non_null,
                        "coverage_pct": coverage,
                        "range": {
                            "min": str(ts_result['min_ts']) if ts_result['min_ts'] else None,
                            "max": str(ts_result['max_ts']) if ts_result['max_ts'] else None
                        }
                    }
                    
                    if non_null < total:
                        msg = f"    ⚠️  {ts_col:20} {coverage:5.1f}% populated"
                        findings["warnings"].append(msg)
                        print(f"    {msg}")
                    else:
                        print(f"    ✓ {ts_col:20} 100% populated")
                    
                    if ts_result['min_ts'] and ts_result['max_ts']:
                        print(f"       Range: {ts_result['min_ts']} → {ts_result['max_ts']}")
        
        except Exception as e:
            findings["error"] = str(e)
            print(f"❌ Timestamp consistency error: {e}")
        
        self.findings["sections"]["timestamp_consistency"] = findings
        return findings
    
    async def audit_data_quality(self):
        """Section 6: Audit data quality and anomalies."""
        print("\n" + "="*80)
        print("6. DATA QUALITY AUDIT")
        print("="*80)
        
        findings = {
            "data_quality_checks": {},
            "anomalies": [],
            "warnings": []
        }
        
        try:
            # Check for duplicate keys
            print("\n🔍 Duplicate key analysis:\n")
            
            # Check for duplicate ponto identifiers within a projeto
            if await self._table_exists("pontos"):
                dup_pontos = await self.connection.fetch_all("""
                    SELECT projeto_id, ponto, COUNT(*) as dup_count
                    FROM pontos
                    GROUP BY projeto_id, ponto
                    HAVING COUNT(*) > 1
                """)
                
                if dup_pontos:
                    findings["anomalies"].extend([{
                        "type": "duplicate_ponto_per_projeto",
                        "count": len(dup_pontos),
                        "details": dup_pontos
                    }])
                    msg = f"⚠️  Found {len(dup_pontos)} duplicate pontos per projeto"
                    findings["warnings"].append(msg)
                    print(f"  {msg}")
                else:
                    print(f"  ✓ No duplicate pontos within projects")
            
            # Check for duplicate niveis_calculo
            if await self._table_exists("niveis_calculo"):
                dup_niveis = await self.connection.fetch_all("""
                    SELECT ponto_id, nivel, COUNT(*) as dup_count
                    FROM niveis_calculo
                    GROUP BY ponto_id, nivel
                    HAVING COUNT(*) > 1
                """)
                
                if dup_niveis:
                    findings["anomalies"].extend([{
                        "type": "duplicate_nivel_per_ponto",
                        "count": len(dup_niveis)
                    }])
                    msg = f"⚠️  Found {len(dup_niveis)} duplicate niveis per ponto"
                    findings["warnings"].append(msg)
                    print(f"  {msg}")
                else:
                    print(f"  ✓ No duplicate niveis per ponto")
            
            # Check for invalid travessias positions
            if await self._table_exists("travessias"):
                invalid_pos = await self.connection.fetch_one("""
                    SELECT COUNT(*) as invalid_count
                    FROM travessias
                    WHERE posicao NOT BETWEEN 1 AND 4
                """)
                
                if invalid_pos['invalid_count'] > 0:
                    msg = f"⚠️  Found {invalid_pos['invalid_count']} invalid travessias positions (not 1-4)"
                    findings["warnings"].append(msg)
                    print(f"  {msg}")
                else:
                    print(f"  ✓ All travessias positions valid (1-4)")
        
        except Exception as e:
            findings["error"] = str(e)
            print(f"❌ Data quality error: {e}")
        
        self.findings["sections"]["data_quality"] = findings
        return findings
    
    async def audit_persistence_layer(self):
        """Section 7: Audit persistence layer (migrations, versions)."""
        print("\n" + "="*80)
        print("7. PERSISTENCE LAYER AUDIT")
        print("="*80)
        
        findings = {
            "migrations": {},
            "schema_version": None,
            "warnings": []
        }
        
        try:
            # Check for alembic_version table (if using Alembic)
            alembic_exists = await self._table_exists("alembic_version")
            
            if alembic_exists:
                version = await self.connection.fetch_all("SELECT version_num FROM alembic_version")
                findings["migrations"]["alembic_versions"] = [v['version_num'] for v in version]
                print(f"\n📝 Alembic migrations applied:\n")
                for v in version:
                    print(f"  • {v['version_num']}")
            else:
                print(f"\n⚫ No alembic_version table found")
                msg = "⚠️  Migration tracking table not found"
                findings["warnings"].append(msg)
            
            # Check for custom version table
            version_tables = await self.connection.fetch_all("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' 
                AND table_name LIKE '%version%'
            """)
            
            if version_tables:
                print(f"\n📜 Version tables found:\n")
                for vt in version_tables:
                    print(f"  • {vt['table_name']}")
        
        except Exception as e:
            findings["error"] = str(e)
            print(f"❌ Persistence layer error: {e}")
        
        self.findings["sections"]["persistence_layer"] = findings
        return findings
    
    async def audit_performance_hints(self):
        """Section 8: Audit for performance issues and missing indexes."""
        print("\n" + "="*80)
        print("8. PERFORMANCE & OPTIMIZATION HINTS")
        print("="*80)
        
        findings = {
            "index_coverage": {},
            "optimization_hints": {},
            "warnings": []
        }
        
        try:
            print("\n⚡ Index coverage analysis:\n")
            
            # Check for indexes on foreign keys
            fk_result = await self.connection.fetch_all("""
                SELECT DISTINCT
                    kcu.table_name,
                    kcu.column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
            """)
            
            print(f"  Foreign keys: {len(fk_result)}")
            
            for fk in fk_result:
                table_name = fk['table_name']
                column_name = fk['column_name']
                
                # Check if indexed
                has_index = await self.connection.fetch_one(f"""
                    SELECT COUNT(*) as cnt
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                        AND tablename = $1
                        AND indexdef LIKE '%{column_name}%'
                """, table_name)
                
                indexed = has_index['cnt'] > 0 if has_index else False
                
                if not indexed:
                    msg = f"    ⚠️  Foreign key {table_name}.{column_name} not indexed"
                    findings["warnings"].append(msg)
                    print(f"    {msg}")
            
            # Check table sizes for missing indexes
            print(f"\n  Table size heuristics:\n")
            
            table_sizes = await self.connection.fetch_all("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_readable,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)
            
            for ts in table_sizes:
                print(f"    • {ts['tablename']:30} {ts['size_readable']:>10}")
        
        except Exception as e:
            findings["error"] = str(e)
            print(f"❌ Performance audit error: {e}")
        
        self.findings["sections"]["performance_hints"] = findings
        return findings
    
    async def _table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        try:
            result = await self.connection.fetch_one("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                        AND table_name = $1
                )
            """, table_name)
            return result[0] if result else False
        except:
            return False
    
    async def _column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if column exists in table."""
        try:
            result = await self.connection.fetch_one("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = 'public'
                        AND table_name = $1
                        AND column_name = $2
                )
            """, table_name, column_name)
            return result[0] if result else False
        except:
            return False
    
    async def _get_table_names(self) -> List[str]:
        """Get all table names."""
        try:
            result = await self.connection.fetch_all("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            return [r['table_name'] for r in result]
        except:
            return []
    
    async def run_all_audits(self):
        """Run all audit sections."""
        try:
            await self.audit_schema_structure()
            await self.audit_data_volume()
            await self.audit_referential_integrity()
            await self.audit_data_completeness()
            await self.audit_timestamp_consistency()
            await self.audit_data_quality()
            await self.audit_persistence_layer()
            await self.audit_performance_hints()
        except Exception as e:
            print(f"❌ Fatal error during audit: {e}")
        
        return self.findings
    
    async def save_report(self, filename: str = "data/reports/persistence_audit_report.json"):
        """Save audit findings to JSON file."""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.findings, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n✓ Report saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save report: {e}")
    
    async def print_summary(self):
        """Print audit summary."""
        print("\n" + "="*80)
        print("AUDIT SUMMARY")
        print("="*80)
        
        total_warnings = 0
        
        for section_name, section_data in self.findings.get("sections", {}).items():
            warnings = section_data.get("warnings", [])
            total_warnings += len(warnings)
            
            status = "✅" if len(warnings) == 0 else f"⚠️  ({len(warnings)})"
            print(f"{status} {section_name}")
        
        print(f"\n📋 Total warnings: {total_warnings}")
        print(f"⏰ Audit completed at: {self.findings['timestamp']}")
        print("\n" + "="*80)


async def main():
    """Main audit execution."""
    load_dotenv()
    
    print("🔍 Starting Persistence Audit...")
    print("="*80)
    
    audit = PersistenceAudit()
    
    try:
        await audit.connect()
        await audit.run_all_audits()
        await audit.print_summary()
        await audit.save_report()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close connection
        if audit.connection:
            try:
                await audit.connection._pool.close()
                print("\n✓ Database connection closed")
            except:
                pass


if __name__ == "__main__":
    asyncio.run(main())
