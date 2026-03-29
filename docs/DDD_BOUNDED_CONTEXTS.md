# DDD Bounded Contexts & Ubiquitous Language

**Date:** 2026-03-25  
**Phase:** 1 — Domain Model Design

---

## Overview: Core Domain Model

Our domain revolves around **electrical distribution network analysis** — specifically, calculating mechanical stress (traction, angle, eccentricity) on utility poles under load from cables.

**Core Concept:** A **Poste** (pole) is the **fundamental unit**. Everything else (geometry, cable types, voltage levels, calculations) is subordinate to understanding and managing a single Poste.

---

## 4 Bounded Contexts

### 1. **Projeto Context** (Project/Owner Container)

**Purpose:** Multi-tenant isolation, project metadata, ownership tracking.

**Ubiquitous Language:**
- **Projeto** (Project) — container for electrical design work, owns responsibility tracking
  - `owner_id` — user who created/owns this project
  - `nome` — project name (user-given)
  - `endereco` — street address of the distribution circuit
  - `orgao` — responsible department/agency
  - `ns` — internal code identifier
  - `data_estudo` — study date
  - Soft-deletable (archived projects remain for audit)

**Aggregates:** `Projeto` (root)

**Key Invariants:**
- A Projeto must have an owner (`owner_id` never null)
- A Projeto can be soft-deleted but never permanently removed
- A Projeto references multiple Postes via IDs (weak coupling)

**Relationships:**
- Projeto 1→N Postes (one-to-many)
- Ownership/Multi-tenancy boundary (Project context enforces tenant isolation)

---

### 2. **Poste Context** (Pole/Distribution Point)

**Purpose:** Model a physical utility pole with all electrical infrastructure, structure, and load calculations.

**Ubiquitous Language:**
- **Poste** (Pole/Post) — physical structure at a geographic point
  - `numero` — user-visible ID (e.g., "P001", "Poste 5", unique per project)
  - `tipo_poste` — construction material (concreto, aço, madeira, DT, etc.)
  - `modelo_poste` — commercial/standard designation (e.g., "11/600" = 11m tall, 600daN capacity)
  - Soft-deletable (removed poles archived with reasoning)

- **Nivel** (Voltage Level) — one of 5 standard distribution tiers on a single Poste
  - Always 5: MT1 (highest), MT2, BT (low voltage), BTZ (low with safety), RAL (additional)
  - `altura_poste` — height of pole crossarm at this level (meters)
  - `altura_ancoragem` — attachment/anchor height (meters) ≤ altura_poste
  - Ordered (MT1 always above MT2 always above BT etc.)

- **Travessia** (Span/Crossing) — conductor(s) crossing between adjacent poles at one Nivel
  - Always 4 positions per Nivel (T1, T2, T3, T4) — for symmetry/standard practice
  - `posicao` — position 1-4 (numbering in distribution standard)
  - **Condutor** — cable/conductor info (type, gauge, connections)
    - `tipo_rede` — circuit type (main, branch, interconnect)
    - `tipo_cabo` — conductor material (AAC, AACSR, Cu, Al, etc.)
    - `qtd_cabos` — number of conductor strands
    - `qtd_ligacoes` — number of electrical connections
  - **Geometria** — geometric span properties
    - `vao` — span distance in meters (center-to-center between poles)
    - `flecha` — sag/dip of conductor under its own weight (meters)
    - `angulo` — deflection angle of conductor (degrees)

- **CalculoSnapshot** (Immutable Calculation Record) — point-in-time result of force calculation
  - **Resultado** (value object) — forces and angles:
    - Per-level: `*_tracao` (tension in daN), `*_angulo` (angle in degrees) for MT1, MT2, BT, BTZ, RAL
    - Totals: `total_tracao`, `total_angulo`
    - `poste_ecc` — pole eccentricity (off-center loading, percent)
    - Text fields: `texto_*` — human-readable output per level
  - `status` — "draft" (working, unsaved) or "saved" (persistent, committed)
  - Immutable (append-only event log of who calculated what when)

- **Geometria_Poste** (Pole Location) — geographic coordinates
  - `latitude`, `longitude` — GPS location (optional)
  - `altura_solo` — above-sea-level height (optional)

**Aggregates:** `Poste` (root), with children `Nivel`, `Travessia`, `CalculoSnapshot`

**Key Invariants:**
- A Poste must have exactly 5 Niveis (MT1, MT2, BT, BTZ, RAL) in that order
- Each Nivel must have exactly 4 Travessias (T1-T4)
- Niveis ordered by altura_poste (decreasing from top to bottom)
- altura_ancoragem ≤ altura_poste for every Nivel
- unique(projeto_id, numero) — no two Postes in same project share numero
- CalculoSnapshots are immutable (only status changes draft→saved, never modifications)
- Only one "current" (most recent saved) calculation per Poste at any time (historical all retained)

**Relationships:**
- Belongs to exactly one Projeto (via projeto_id reference)
- Each Nivel "belongs" logically to the Poste (composition)
- Each Travessia belongs to a Nivel (composition nesting)
- CalculoSnapshots form ordered history (by calculado_em timestamp)

---

### 3. **Calculo Context** (Stateless Calculation Engine)

**Purpose:** Pure mathematical/physical calculation divorced from state. Input→ Output, no side effects.

**Ubiquitous Language:**
- **CalculoInput** — specification of a single Poste's current geometry
  - `ponto_id` — which pole to calculate
  - `niveis` array — current geometry of all levels
    - For each Nivel: altura_poste, altura_ancoragem, travessias array
      - For each Travessia: vao, flecha, angulo, (implicitly conductor properties from last saved)

- **CalculoOutput** (same as **CalculoResultado**) — forces, angles, eccentricity
  - Stateless; calculated fresh every time input changes

**Boundary:** 
- Input: Geometry from Poste context → compute → Output: forces/angles
- No state (is stateless utility, not an aggregate)
- Reusable across contexts (also used in reporting, exports, etc.)

**Key Properties:**
- Deterministic (same input → same output always)
- No persistence (calculated on-demand or externally stored by Poste context)
- No domain rules (math only; domain validation happens before/after)

---

### 4. **Auditoria Context** (Event Logging & Compliance)

**Purpose:** Track all domain events for audit trail, compliance, data analysis.

**Ubiquitous Language:**
- **DomainEvent** — immutable record of what happened
  - `event_id` — UUID, globally unique
  - `aggregate_id` — which Poste or Projeto was affected
  - `aggregate_type` — "Poste" or "Projeto"
  - `timestamp` — when it happened
  - `user_id` — who did it
  - Event-specific fields (e.g., "PosteCriado" includes numero, tipo_poste, etc.)

**Event Types:**
- `ProjetoCriado` — Projeto created (nome, owner, endereco, orgao, ns)
- `PosteCriado` — Poste created (numero, tipo_poste, modelo_poste)
- `NivelAtualizado` — Geometry of a Nivel changed
- `TravessiaAtualizada` — Geometry/conductor of a Travessia changed
- `CalculoSnapshot` — Calculation performed (resultado_json, status=draft/saved)
- `CalculoDeletado` — Calculation soft-deleted
- `PosteDeletado` — Poste soft-deleted (razao recorded)
- `ProjetoDeletado` — Projeto soft-deleted (razao recorded)

**Storage:** (In Phase 3) Persisted in `calculo_snapshots_events` table (append-only log)

**Key Properties:**
- Immutable (events never edited, only appended)
- Ordered by timestamp (can replay history)
- User-traceable (user_id captured)
- Reason/context (soft-deletes record "why")

---

## Ubiquitous Language — Glossary

| Term | Definition | Context |
|------|-----------|---------|
| **Poste** | Physical utility pole with electrical infrastructure | Poste Context |
| **Projeto** | Container project for multi-poste design study | Projeto Context |
| **Nivel** | One of 5 voltage levels on a Poste (MT1, MT2, BT, BTZ, RAL) | Poste Context |
| **Travessia** | Conductor/cable span between two adjacent poles at one Nivel | Poste Context |
| **Vão** (Span) | Horizontal distance between adjacent pole centers (meters) | Poste Context (Geometria) |
| **Flecha** (Sag) | Vertical dip of conductor under its own weight (meters) | Poste Context (Geometria) |
| **Tração** (Tension) | Mechanical force on conductor/pole (daNs — decanewtons) | Poste Context (Resultado) |
| **Ângulo** (Angle) | Angle of conductor deviation from horizontal (degrees) | Poste Context (Resultado) |
| **Excentricidade do Poste** | Off-center loading (pole tip deflection, percent) | Poste Context (Resultado) |
| **Condutor** | Cable type, gauge, connections | Poste Context (Travessia) |
| **Rede** | Circuit designation (main, branch, interconnection) | Poste Context |
| **Cálculo** | Mechanical calculation output (forces, angles, eccentricity) | Calculo Context |
| **Snapshot** | Point-in-time immutable record of calculation (draft or saved) | Poste Context (CalculoSnapshot) |
| **Soft-delete** | Mark as deleted (keep for audit, hide from UI) | All contexts |

---

## Cross-Context Communication

### Projeto →  Poste Context
- Projeto holds list of PosteIds (references, not embedded)
- No direct ownership of Poste data
- Creates/deletes Postes through Poste aggregate operations
- **Pattern:** Commands like "DeletePoste(projeto_id, poste_id)" validated at Projeto boundary

### Poste → Calculo Context
- Poste fetches its current Geometria
- Calls stateless Calculo engine (e.g., `calcular(ponto_id, niveis_input)`)
- Receives CalculoOutput (doesn't persist it into Calculo context)
- Wraps result in CalculoSnapshot (immutable event, appended to Poste history)
- **Pattern:** Query-only; no shared mutable state

### Poste → Auditoria Context
- Poste generates DomainEvents (PosteCriado, NivelAtualizado, etc.)
- No bi-directional dependency
- Events published/persisted in separate event log (Phase 3)
- **Pattern:** One-way publish; Auditoria is read-only

### Projeto → Auditoria Context
- Similar: ProjetoCriado, ProjetoDeletado events published
- One-way; no dependency on Auditoria

### Cross-Project Poste Lineage
A physical utility pole may appear in **multiple Projects** over time.  
When Project Y begins from a pole already studied in Project X, a lineage
link is established:

```
Poste (Project X, numero="7")  ←── origem_id  ── Poste (Project Y, numero="5")
```

**Rules:**
- `Poste.origem_id` is a nullable self-referential FK on the `pontos` table.
- Only set when a Poste is explicitly declared a continuation of another.
- The two Postes must belong to **different** projects.
- **Latest-timestamp-wins:** the Poste with the most recent `atualizado_em`
  holds the authoritative state of that physical pole.
- Audit queries traverse the chain using `GET /postes/{id}/linhagem`.

**Domain event:** `PosteVinculado` — recorded whenever a lineage link is created.

**Data model:**
```
pontos
  id               UUID PK
  projeto_id       UUID FK → projetos.id
  poste_origem_id  UUID FK → pontos.id (nullable, self-referential)
  ...

calculos_snapshots
  id          UUID PK
  poste_id    UUID FK → pontos.id
  projeto_id  UUID FK → projetos.id  ← NEW: explicit project attribution
  ...
```

**API surface:**
| Endpoint | Purpose |
|---|---|
| `PUT /postes/{id}/vincular-origem` | Link Poste to predecessor |
| `GET /postes/{id}/linhagem` | Return full ancestry chain |

---

## Invariants Summary

### Poste Aggregate Invariants
1. **Exactly 5 Niveis:** MT1, MT2, BT, BTZ, RAL in order (Nivel.ordem() enforces)
2. **Each Nivel: 4 Travessias** at positions 1-4
3. **Unique Poste Numero per Projeto:** (projeto_id, numero) unique
4. **Ordered Niveis by Height:** altura_poste decreases from MT1 to RAL
5. **Anchor ≤ Pole Height:** altura_ancoragem ≤ altura_poste for each Nivel
6. **CalculoSnapshot Immutability:** Once created, never modified (only status: draft→saved)
7. **Soft-Delete:** deletado_em timestamp; not truly removed for audit

### Projeto Aggregate Invariants
1. **Owner Required:** owner_id not null/empty
2. **Name Required:** nome not null/empty
3. **Unique Projeto per Owner:** (owner_id, ns or nome) likely unique (business rule, not enforced here)
4. **Soft-Delete:** deletado_em timestamp; not truly removed

### Cross-Aggregate Invariants
1. **Referential Integrity:** Every PosteId in Projeto.poste_ids must exist as a Poste
2. **No Orphans:** Deleted Postes removed from Projeto.poste_ids (or marked in event)
3. **Tenant Isolation:** User never sees Postes from other projects (enforced at Repository/API level)

---

## API Contract (Preview — Phase 3 Detail)

*Note: Full API specification in Phase 3. Here's the domain contract.*

**Create Project:**
```
POST /projetos
{
 "nome": "Projeto Light - Rua X",
 "endereco": "Rua X nº 100",
 "orgao": "LIGHT S.A.",
 "ns": "LT-RJ-001",
 "estudado_por": "Eng. Silva",
 "matricula": "E001"
}
→ ProjetoCriado event
→ Projeto aggregate created & persisted
```

**Create Poste in Project:**
```
POST /projetos/{projeto_id}/postes
{
  "numero": "P001",
  "tipo_poste": "concreto",
  "modelo_poste": "11/600"
}
→ PosteCriado event
→ Poste aggregate created with 5 empty Niveis (4 Travessias each)
```

**Perform Calculation:**
```
POST /postes/{poste_id}/calcular
{
  "niveis": [
    {
      "nivel": "MT1",
      "altura_poste": 11.0,
      "altura_ancoragem": 9.2,
      "travessias": [
        {"posicao": 1, "vao": 15.0, "flecha": 0.5, "angulo": 10.0, ...},
        ...
      ]
    },
    ...
  ]
}
→ CalculoSnapshot event (status=draft)
→ CalculoSnapshotEvent recorded (immutable)
```

**Save Calculation:**
```
POST /postes/{poste_id}/calculos/{calculo_id}/salvar
→ CalculoSnapshot status changed to "saved" (immutable append, new record)
→ CalculoSnapshot event re-published with status=saved
```

---

## Phase Roadmap (How This Fits In)

- **Phase 1 (done):** Domain model + bounded contexts (this document)
- **Phase 2:** Database schema (map aggregates → tables)
- **Phase 3:** API layer (repository, services, HTTP routes)
- **Phase 4:** Frontend (React hooks to consume API)
- **Phases 5-6:** Migration + release

All domain code is pure Python, no DB, no HTTP. Ready for any persistence strategy (SQL, NoSQL, event-sourced, etc.).
