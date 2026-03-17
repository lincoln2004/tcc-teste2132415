from typing import List
import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.dependencias.autenticacao import obter_usuario_atual
from app.esquemas.analise_esquema import AnaliseCriar, AnaliseResposta
from app.modelos.usuario import Usuario
from app.repositorios.analise_repositorio import AnaliseRepositorio
from app.servicos.analise_servico import AnaliseServico


router = APIRouter()


@router.post("/executar", response_model=AnaliseResposta, status_code=status.HTTP_201_CREATED)
async def executar_analise(
    analise_in: AnaliseCriar,
    usuario_atual: Usuario = Depends(obter_usuario_atual),
) -> AnaliseResposta:
    """
    Cria e dispara a execucao de uma nova analise de anomalias.
    """
    try:
        return await AnaliseServico.criar_e_executar_analise(analise_in, usuario_atual.id)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro)) from erro
    except Exception as erro:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar analise: {erro}",
        ) from erro


@router.get("/historico", response_model=List[AnaliseResposta])
async def listar_historico(usuario_atual: Usuario = Depends(obter_usuario_atual)) -> List[AnaliseResposta]:
    """
    Retorna o historico de analises realizadas pelo usuario autenticado.
    """
    return await AnaliseRepositorio.listar_por_usuario(usuario_atual.id)


@router.delete("/historico", status_code=status.HTTP_200_OK)
async def excluir_historico(usuario_atual: Usuario = Depends(obter_usuario_atual)) -> dict[str, int | str]:
    """
    Remove todo o historico de analises do usuario autenticado.
    """
    return await AnaliseServico.excluir_historico_usuario(usuario_atual.id)


@router.get("/{analise_id}", response_model=AnaliseResposta)
async def obter_detalhes_analise(
    analise_id: int,
    usuario_atual: Usuario = Depends(obter_usuario_atual),
) -> AnaliseResposta:
    """
    Obtem os detalhes de uma analise especifica pertencente ao usuario logado.
    """
    analise = await AnaliseRepositorio.obter_por_id_e_usuario(analise_id, usuario_atual.id)
    if not analise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analise nao encontrada.")
    return analise


@router.get("/{analise_id}/download")
async def baixar_resultado_analise(
    analise_id: int,
    usuario_atual: Usuario = Depends(obter_usuario_atual),
) -> FileResponse:
    """
    Disponibiliza o CSV gerado pela analise concluida para o usuario autenticado.
    """
    analise = await AnaliseRepositorio.obter_por_id_e_usuario(analise_id, usuario_atual.id)
    if not analise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analise nao encontrada.")
    if not analise.caminho_resultado_csv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A analise ainda nao possui um arquivo de resultado disponivel.",
        )
    if not os.path.exists(analise.caminho_resultado_csv):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O arquivo de resultado da analise nao foi encontrado no armazenamento local.",
        )
    return FileResponse(
        analise.caminho_resultado_csv,
        media_type="text/csv",
        filename=f"resultado_analise_{analise.id}.csv",
    )
