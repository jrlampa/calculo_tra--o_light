"""Pydantic models for projeto operations."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class ProjetoBase(BaseModel):
    """Base schema for projeto."""
    orgao: str = Field(..., min_length=1, max_length=100)
    ns: str = Field(..., min_length=1, max_length=20)
    nome: str = Field(..., min_length=1, max_length=200)
    endereco: Optional[str] = Field(None, max_length=500)
    estudado_por: str = Field(..., min_length=1, max_length=100)
    matricula: str = Field(..., min_length=1, max_length=20)
    data_estudo: Optional[datetime] = None
    
    @validator('data_estudo', pre=True, always=True)
    def set_default_data_estudo(cls, v):
        return v or datetime.utcnow()


class ProjetoCreate(ProjetoBase):
    """Schema for creating a projeto."""
    owner_id: UUID
    
    @validator('orgao', 'ns', 'nome', 'estudado_por')
    def normalize_string(cls, v):
        return v.strip().title()


class ProjetoUpdate(BaseModel):
    """Schema for updating a projeto."""
    orgao: Optional[str] = Field(None, min_length=1, max_length=100)
    ns: Optional[str] = Field(None, min_length=1, max_length=20)
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    endereco: Optional[str] = Field(None, max_length=500)
    estudado_por: Optional[str] = Field(None, min_length=1, max_length=100)
    matricula: Optional[str] = Field(None, min_length=1, max_length=20)
    data_estudo: Optional[datetime] = None
    
    @validator('orgao', 'ns', 'nome', 'estudado_por')
    def normalize_string(cls, v):
        if v is not None:
            return v.strip().title()
        return v


class ProjetoInDBBase(ProjetoBase):
    """Base schema for projeto in database."""
    id: UUID
    owner_id: UUID
    total_pontos: int = 0
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


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
