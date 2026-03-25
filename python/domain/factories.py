"""Factory functions for Poste aggregate conversion.

Convert between:
1. API schemas (CalculoInput, etc) → Domain aggregates
2. Domain aggregates → Response DTOs
3. DB models → Domain aggregates (handled by PosteRepository)
"""
from __future__ import annotations

from typing import List
from uuid import UUID

from api.schemas import CalculoInput, CabecalhoIn, PosteIn, MTTraversalIn, BTTraversalIn
from domain.aggregates import Poste as PosteAggregate, Nivel as NivelEntity, Travessia as TravessiaEntity
from domain.value_objects import (
    Condutor, Geometria, NivelEnum, PosteId, ProjetoId,
    CaboConductor, TipoRede,
)


class PosteFactory:
    """Factory for creating and converting Poste aggregates."""
    
    @staticmethod
    def from_calculo_input(
        projeto_id: UUID,
        calculo_input: CalculoInput
    ) -> PosteAggregate:
        """Convert CalculoInput (from frontend) to domain Poste aggregate.
        
        This factory:
        1. Extracts Poste data from cabecalho + poste fields
        2. Builds 5 niveis with traversals from MT1/MT2/BT/BTZ/RAL lists
        3. Creates domain aggregate with proper validation
        """
        cabecalho = calculo_input.cabecalho
        poste_in = calculo_input.poste
        
        # Extract numero from cabecalho
        numero = cabecalho.numero or "UNKNOWN"
        
        # Create 5 niveis from input lists
        niveis = [
            PosteFactory._criar_nivel(NivelEnum.MT1, calculo_input.mt1, cabecalho),
            PosteFactory._criar_nivel(NivelEnum.MT2, calculo_input.mt2, cabecalho),
            PosteFactory._criar_nivel(NivelEnum.BT, calculo_input.bt, cabecalho),
            PosteFactory._criar_nivel(NivelEnum.BTZ, calculo_input.btz, cabecalho),
            PosteFactory._criar_nivel(NivelEnum.RAL, calculo_input.ral, cabecalho),
        ]
        
        # Create Poste aggregate
        poste = PosteAggregate(
            projeto_id=ProjetoId(value=projeto_id),
            numero=numero,
            niveis=niveis,
            tipo_poste=poste_in.tipo_poste,
            modelo_poste=poste_in.modelo_poste
        )
        
        return poste
    
    @staticmethod
    def _criar_nivel(
        nivel_enum: NivelEnum,
        traversals: List,  # MTTraversalIn | BTTraversalIn | RamaisTraversalIn
        cabecalho: CabecalhoIn
    ) -> NivelEntity:
        """Create a Nivel entity from traversal list + cabecalho geometry hints."""
        
        # Use first traversal's altura_poste/altura_ancoragem as defaults
        altura_poste = traversals[0].altura_poste if traversals else 11.0
        altura_ancoragem = traversals[0].altura_ancoragem if traversals else 9.2
        
        # Create 4 Travessias from input list
        travessias = [
            PosteFactory._criar_travessia(nivel_enum, i + 1, traversals[i])
            for i in range(4)
        ]
        
        nivel = NivelEntity(
            nivel_enum=nivel_enum,
            altura_poste=altura_poste,
            altura_ancoragem=altura_ancoragem,
            travessias=travessias
        )
        
        return nivel
    
    @staticmethod
    def _criar_travessia(
        nivel_enum: NivelEnum,
        posicao: int,
        traversal_in
    ) -> TravessiaEntity:
        """Create a Travessia from API traversal input."""
        
        # Safely extract fields (may be None or empty)
        tipo_rede = getattr(traversal_in, 'tipo_rede', '')
        tipo_cabo = getattr(traversal_in, 'tipo_cabo', '')
        vao = getattr(traversal_in, 'vao', 0.0) or 0.0
        flecha = getattr(traversal_in, 'flecha', 0.0) or 0.0
        angulo = getattr(traversal_in, 'angulo', 0.0) or 0.0
        
        condutor = Condutor(
            tipo=PosteFactory._parse_tipo_cabo(tipo_cabo),
            tipo_rede=PosteFactory._parse_tipo_rede(tipo_rede)
        )
        
        geometria = Geometria(
            vao=max(0, vao),
            flecha=max(0, flecha),
            angulo=angle % 360 if (angle := angulo) >= 0 else (360 + angulo % 360)
        )
        
        travessia = TravessiaEntity(
            posicao=posicao,
            condutor=condutor,
            geometria=geometria
        )
        
        return travessia
    
    @staticmethod
    def _parse_tipo_cabo(tipo_cabo_str: str) -> CaboConductor:
        """Parse cable type string to CaboConductor enum.
        
        Common patterns:
        - "CAA" or "397MCM-CA" → CaboConductor.CAA
        - "AACSR" or "MCM-AACSR" → CaboConductor.AACSR
        - "Neutro" or "cabo neutro" → CaboConductor.NEUTRO
        - "TERRA" or "terra" → CaboConductor.TERRA
        """
        s = (tipo_cabo_str or "").upper()
        
        if not s or s == "CAA":
            return CaboConductor.CAA
        elif "AACSR" in s:
            return CaboConductor.AACSR
        elif "NEUTRO" in s or s == "NEUTRO":
            return CaboConductor.NEUTRO
        elif "TERRA" in s or s == "TERRA":
            return CaboConductor.TERRA
        elif "CU" in s or s == "CU":
            return CaboConductor.CU
        elif "AL" in s or s == "AL":
            return CaboConductor.AL
        else:
            # Default to CAA for unknown
            return CaboConductor.CAA
    
    @staticmethod
    def _parse_tipo_rede(tipo_rede_str: str) -> TipoRede:
        """Parse network type string to TipoRede enum.
        
        Common patterns:
        - "Circuito" or "CIRCUITO" → TipoRede.CIRCUITO
        - "Ramificação" or "RAMIFICACAO" → TipoRede.RAMIFICACAO
        - "Interligação" or "INTERLIGACAO" → TipoRede.INTERLIGACAO
        """
        s = (tipo_rede_str or "").upper()
        
        if not s or "CIRCUITO" in s:
            return TipoRede.CIRCUITO
        elif "RAMIF" in s:
            return TipoRede.RAMIFICACAO
        elif "INTERLIG" in s:
            return TipoRede.INTERLIGACAO
        else:
            # Default to circuito
            return TipoRede.CIRCUITO
    
    @staticmethod
    def to_response_dict(poste: PosteAggregate) -> dict:
        """Convert Poste aggregate to response DTO (JSON-serializable dict).
        
        Used for API responses when returning Poste details.
        """
        return {
            'id': str(poste.id.value),
            'projeto_id': str(poste.projeto_id.value),
            'numero': poste.numero,
            'tipo_poste': poste.tipo_poste,
            'modelo_poste': poste.modelo_poste,
            'criado_em': poste.criado_em.isoformat() if poste.criado_em else None,
            'atualizado_em': poste.atualizado_em.isoformat() if poste.atualizado_em else None,
            'deletado_em': poste.deletado_em.isoformat() if poste.deletado_em else None,
            'niveis': [
                {
                    'nivel': n.nivel_enum.value,
                    'altura_poste': n.altura_poste,
                    'altura_ancoragem': n.altura_ancoragem,
                    'travessias': [
                        {
                            'posicao': t.posicao,
                            'tipo_rede': t.condutor.tipo_rede.value,
                            'tipo_cabo': t.condutor.tipo.value,
                            'vao': t.geometria.vao,
                            'flecha': t.geometria.flecha,
                            'angulo': t.geometria.angulo,
                        }
                        for t in n.travessias
                    ]
                }
                for n in poste.niveis
            ]
        }
