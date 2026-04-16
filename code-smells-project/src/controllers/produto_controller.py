from flask import request, jsonify
from src.models import produto_model

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]


def _validar_payload_produto(dados):
    if not dados:
        return "Dados inválidos"
    if "nome" not in dados:
        return "Nome é obrigatório"
    if "preco" not in dados:
        return "Preço é obrigatório"
    if "estoque" not in dados:
        return "Estoque é obrigatório"
    if dados["preco"] < 0:
        return "Preço não pode ser negativo"
    if dados["estoque"] < 0:
        return "Estoque não pode ser negativo"
    if len(dados["nome"]) < 2:
        return "Nome muito curto"
    if len(dados["nome"]) > 200:
        return "Nome muito longo"
    categoria = dados.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        return f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}"
    return None


def listar_produtos():
    produtos = produto_model.get_todos_produtos()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id):
    produto = produto_model.get_produto_por_id(id)
    if produto:
        return jsonify({"dados": produto, "sucesso": True}), 200
    return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404


def criar_produto():
    dados = request.get_json()
    erro = _validar_payload_produto(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    id = produto_model.criar_produto(
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral")
    )
    return jsonify({"dados": {"id": id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    produto_existente = produto_model.get_produto_por_id(id)
    if not produto_existente:
        return jsonify({"erro": "Produto não encontrado"}), 404

    dados = request.get_json()
    erro = _validar_payload_produto(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    produto_model.atualizar_produto(
        id,
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral")
    )
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    produto = produto_model.get_produto_por_id(id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404
    produto_model.deletar_produto(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)

    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)

    resultados = produto_model.buscar_produtos(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
