from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.dependencias.autenticacao import obter_usuario_atual
from app.esquemas.dataset_esquema import DatasetResposta
from app.modelos.usuario import Usuario
from app.repositorios.dataset_repositorio import DatasetRepositorio
from app.servicos.dataset_servico import DatasetServico


router = APIRouter()


@router.post("/upload", response_model=DatasetResposta, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    nome: str = Form(...),
    descricao: Optional[str] = Form(None),
    arquivo: UploadFile = File(...),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
) -> DatasetResposta:
    """
    Realiza o upload de um novo arquivo CSV ou Excel para o usuario autenticado.
    """
    try:
        return await DatasetServico.salvar_dataset(arquivo, nome, descricao, usuario_atual.id)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro)) from erro


@router.get("/", response_model=List[DatasetResposta])
async def listar_datasets(usuario_atual: Usuario = Depends(obter_usuario_atual)) -> List[DatasetResposta]:
    """
    Lista todos os datasets pertencentes ao usuario autenticado.
    """
    return await DatasetServico.listar_datasets(usuario_atual.id)


@router.get("/{dataset_id}", response_model=DatasetResposta)
async def obter_dataset(dataset_id: int, usuario_atual: Usuario = Depends(obter_usuario_atual)) -> DatasetResposta:
    """
    Retorna os detalhes de um dataset especifico pertencente ao usuario logado.
    """
    dataset = await DatasetRepositorio.obter_por_id_e_usuario(dataset_id, usuario_atual.id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset nao encontrado.")
    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_200_OK)
async def excluir_dataset(dataset_id: int, usuario_atual: Usuario = Depends(obter_usuario_atual)) -> dict[str, int | str]:
    """
    Exclui um dataset do usuario autenticado e remove analises relacionadas.
    """
    try:
        return await DatasetServico.excluir_dataset(dataset_id, usuario_atual.id)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(erro)) from erro
