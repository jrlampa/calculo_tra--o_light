"""Pydantic models for projeto operations."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProjetoBase(BaseModel):
    """Base schema for projeto."""
    orgao: str = Field(default="", max_length=100)
    ns: str = Field(default="", max_length=20)
    nome: str = Field(..., min_length=1, max_length=200)  # Campo obrigatório
    endereco: Optional[str] = Field(default="", max_length=500)
    estudado_por: str = Field(default="", max_length=100)
    matricula: str = Field(default="", max_length=20)
    data_estudo: Optional[str] = None
    
    @field_validator('data_estudo', mode='before')
    @classmethod
    def set_default_data_estudo(cls, v):
        if not v:
            return datetime.now(UTC).strftime("%d/%m/%Y")
        if isinstance(v, datetime):
            return v.strftime("%d/%m/%Y")
        return v
    
    @field_validator('data_estudo')
    @classmethod
    def validate_data_estudo(cls, v):
        if not v:
            return v
        
        try:
            # Validar formato da data
            dt = datetime.strptime(v, "%d/%m/%Y")
            
            # Validar que a data não está no futuro
            if dt.date() > datetime.now(UTC).date():
                raise ValueError("Data de estudo não pode estar no futuro")
                
            return v
        except ValueError as e:
            if "future" in str(e):
                raise ValueError("Data de estudo não pode estar no futuro")
            raise ValueError("Formato de data inválido. Use DD/MM/AAAA")


class ProjetoCreate(ProjetoBase):
    """Schema for creating a projeto."""
    owner_id: UUID
    
    @field_validator('orgao', 'ns', 'nome', 'estudado_por')
    @classmethod
    def normalize_string(cls, v):
        return v.strip()


class ProjetoUpdate(BaseModel):
    """Schema for updating a projeto."""
    orgao: Optional[str] = Field(None, min_length=1, max_length=100)
    ns: Optional[str] = Field(None, min_length=1, max_length=20)
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    endereco: Optional[str] = Field(None, max_length=500)
    estudado_por: Optional[str] = Field(None, min_length=1, max_length=100)
    matricula: Optional[str] = Field(None, min_length=1, max_length=20)
    data_estudo: Optional[str] = None
    
    @field_validator('orgao', 'ns', 'nome', 'estudado_por')
    @classmethod
    def normalize_string(cls, v):
        if v is not None:
            return v.strip()
        return v


class ProjetoInDBBase(ProjetoBase):
    """Base schema for projeto in database."""
    id: UUID
    owner_id: UUID
    total_pontos: int = 0
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @model_validator(mode='before')
    @classmethod
    def normalize_timestamp_contract(cls, values):
        """Support both EN and PT-BR timestamp column contracts."""
        if not isinstance(values, dict):
            return values

        if values.get("created_at") is None and values.get("criado_em") is not None:
            values["created_at"] = values["criado_em"]

        if values.get("updated_at") is None and values.get("atualizado_em") is not None:
            values["updated_at"] = values["atualizado_em"]

        if values.get("deleted_at") is None and values.get("deletado_em") is not None:
            values["deleted_at"] = values["deletado_em"]

        return values
    
    model_config = ConfigDict(from_attributes=True)


class Projeto(ProjetoInDBBase):
    """Complete projeto schema."""
    pass


class ProjetoOut(ProjetoInDBBase):
    """Schema for projeto output."""
    pass


class ProjetoList(BaseModel):
    """Schema for list of projetos."""
    projetos: list[ProjetoOut]
    total: int
    page: int
    per_page: int
