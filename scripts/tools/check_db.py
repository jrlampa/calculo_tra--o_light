import asyncio
import os
import sys
from uuid import UUID

# Add python to path
sys.path.append(os.path.join(os.getcwd(), "python"))

from db.pool import initialize_db_pool, get_database

async def check():
    await initialize_db_pool()
    db = await get_database()
    from repositories.projeto_repository import ProjetoRepository
    repo = ProjetoRepository(db)
    
    print("=== AUDIT: LAST PROJETOS IN DB ===")
    projetos = await repo.get_multi()
    # Sort by created_at desc if possible
    # Pydantic models from ProjetoRepository.get_multi have created_at
    for p in sorted(projetos, key=lambda x: x.created_at, reverse=True)[:10]:
        print(f"ID: {p.id} | Name: {p.nome} | Org: {p.orgao} | Created: {p.created_at}")

if __name__ == "__main__":
    asyncio.run(check())
