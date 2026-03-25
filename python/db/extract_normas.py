"""Extract rules and standards from LIGHT reference documents."""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

LIGHT_FOLDER = r"C:\Users\jonat\OneDrive - IM3 Brasil\LIGHT\Arquivos para auxílio"


def extract_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract text from PDF using pdfplumber."""
    try:
        import pdfplumber

        normas = []

        with pdfplumber.open(pdf_path) as pdf:
            filename = Path(pdf_path).name

            # Determine category from filename
            categoria = "Padrão Geral"
            if "Compacta" in filename:
                categoria = "Padrão Rede Compacta"
            elif "Convencional" in filename:
                categoria = "Padrão Rede Convencional"
            elif "Equipamentos" in filename:
                categoria = "Padrão de Equipamentos"
            elif "MTX BT" in filename:
                categoria = "Padrão Rede MTX BT"
            elif "MTX MT" in filename:
                categoria = "Padrão Rede MTX MT"

            full_text = ""
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    full_text += f"\n--- Page {page_num} ---\n{text}"

            # Parse into logical sections
            normas_parsed = _parse_pdf_content(full_text, categoria, filename)
            normas.extend(normas_parsed)

        return normas
    except ImportError:
        print(f"⚠️ pdfplumber not installed. Run: pip install pdfplumber")
        return []
    except Exception as e:
        print(f"❌ Error extracting from {pdf_path}: {e}")
        return []


def extract_from_docx(docx_path: str) -> List[Dict[str, Any]]:
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document

        normas = []

        filename = Path(docx_path).name
        categoria = "Roteiro de Projetos"

        doc = Document(docx_path)

        # Extract all paragraphs and tables
        content = []
        for para in doc.paragraphs:
            if para.text.strip():
                content.append(para.text)

        # Parse into rules/sections
        for i, line in enumerate(content):
            if len(line) > 20:  # Significant text
                normas.append(
                    {
                        "categoria": categoria,
                        "arquivo_origem": filename,
                        "titulo": _extract_title(line),
                        "descricao": line,
                        "regra_tecnica": None,
                        "aplicavel_a": "RDA urbanas",
                        "fonte_referencia": f"MINUTA LIGHT",
                    }
                )

        return normas
    except ImportError:
        print(f"⚠️ python-docx not installed. Run: pip install python-docx")
        return []
    except Exception as e:
        print(f"❌ Error extracting from {docx_path}: {e}")
        return []


def extract_from_xlsx(xlsx_path: str) -> List[Dict[str, Any]]:
    """Extract specifications from Excel files."""
    try:
        from openpyxl import load_workbook

        normas = []

        filename = Path(xlsx_path).name
        categoria = "Cadastro de Materiais"
        if "CÁLCULO DE TRAÇÃO" in filename.upper():
            categoria = "Padrão de Tração"

        wb = load_workbook(xlsx_path, data_only=True)

        for sheet in wb.sheetnames[:3]:  # First 3 sheets
            ws = wb[sheet]

            # Extract header and data
            rows = list(ws.iter_rows(values_only=True))
            if len(rows) > 1:
                header = rows[0]
                for row in rows[1:10]:  # First few data rows
                    if any(row):
                        normas.append(
                            {
                                "categoria": categoria,
                                "arquivo_origem": filename,
                                "titulo": f"Especificação {sheet}",
                                "descricao": " | ".join(str(v) for v in row if v),
                                "regra_tecnica": str(header) if header else None,
                                "aplicavel_a": "Materiais e Equipamentos",
                                "fonte_referencia": f"Aba: {sheet}",
                            }
                        )

        return normas
    except ImportError:
        print(f"⚠️ openpyxl not installed. Run: pip install openpyxl")
        return []
    except Exception as e:
        print(f"❌ Error extracting from {xlsx_path}: {e}")
        return []


def _extract_title(text: str) -> str:
    """Extract a title from text (first 100 chars)."""
    title = text.strip()
    if len(title) > 100:
        title = title[:97] + "..."
    return title


def _parse_pdf_content(text: str, categoria: str, filename: str) -> List[Dict[str, Any]]:
    """Parse PDF extracted text into structured rules."""
    normas = []

    # Split by common delimiters
    sections = text.split("---")

    for section in sections:
        lines = section.strip().split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            if line and len(line) > 20:  # Meaningful text
                # Group 2-3 lines as a rule
                descricao = line
                if i + 1 < len(lines):
                    descricao += " " + lines[i + 1].strip()

                normas.append(
                    {
                        "categoria": categoria,
                        "arquivo_origem": filename,
                        "titulo": _extract_title(line),
                        "descricao": descricao,
                        "regra_tecnica": None,
                        "aplicavel_a": categoria.replace("Padrão ", ""),
                        "fonte_referencia": f"LIGHT {categoria}",
                    }
                )

    return normas[:50]  # Limit to 50 entries per file


def collect_all_normas() -> List[Dict[str, Any]]:
    """Collect all rules from LIGHT reference folder."""
    all_normas = []

    if not os.path.exists(LIGHT_FOLDER):
        print(f"❌ LIGHT folder not found: {LIGHT_FOLDER}")
        return all_normas

    print(f"📂 Extracting from: {LIGHT_FOLDER}\n")

    for filename in os.listdir(LIGHT_FOLDER):
        filepath = os.path.join(LIGHT_FOLDER, filename)

        if filename.endswith(".pdf"):
            print(f"📄 Extracting PDF: {filename}...")
            normas = extract_from_pdf(filepath)
            all_normas.extend(normas)
            print(f"   ✅ {len(normas)} entries extracted")

        elif filename.endswith(".docx"):
            print(f"📄 Extracting DOCX: {filename}...")
            normas = extract_from_docx(filepath)
            all_normas.extend(normas)
            print(f"   ✅ {len(normas)} entries extracted")

        elif filename.endswith((".xlsx", ".xls")):
            if "CADASTRO" in filename.upper() or "CÁLCULO" in filename.upper():
                print(f"📊 Extracting Excel: {filename}...")
                normas = extract_from_xlsx(filepath)
                all_normas.extend(normas)
                print(f"   ✅ {len(normas)} entries extracted")

    return all_normas


async def insert_normas_to_supabase(normas: List[Dict[str, Any]]) -> bool:
    """Insert extracted normas into Supabase using asyncpg."""
    try:
        import asyncpg
        from dotenv import load_dotenv

        load_dotenv()

        database_url = os.getenv("DATABASE_URL", "")

        if not database_url:
            print("⚠️ DATABASE_URL not configured in .env")
            print("✅ Normas extracted but not inserted to database")
            return False

        try:
            conn = await asyncpg.connect(database_url)
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False

        try:
            inserted = 0
            for norma in normas:
                try:
                    await conn.execute(
                        """INSERT INTO normas_regras 
                        (categoria, arquivo_origem, titulo, descricao, regra_tecnica, aplicavel_a, fonte_referencia) 
                        VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                        norma.get("categoria"),
                        norma.get("arquivo_origem"),
                        norma.get("titulo"),
                        norma.get("descricao"),
                        norma.get("regra_tecnica"),
                        norma.get("aplicavel_a"),
                        norma.get("fonte_referencia"),
                    )
                    inserted += 1
                except asyncpg.exceptions.UniqueViolationError:
                    pass  # Skip duplicates
                except Exception as e:
                    print(f"⚠️ Error inserting norma: {e}")

            print(f"\n✅ {inserted} normas inserted to Supabase")
            return inserted > 0

        finally:
            await conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def save_normas_to_json(normas: List[Dict[str, Any]], output_file: str = "data/artifacts/normas_extracted.json"):
    """Save extracted normas to JSON file for backup."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(normas, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved to {output_file}")


if __name__ == "__main__":
    print("🔍 Extracting normas and rules from LIGHT reference documents...\n")

    # Collect all normas
    normas = collect_all_normas()

    print(f"\n📊 Total extracted: {len(normas)} norms/rules")

    # Save to JSON
    save_normas_to_json(normas)

    # Insert to Supabase
    import asyncio

    print("\n📤 Inserting into Supabase...")
    asyncio.run(insert_normas_to_supabase(normas))
