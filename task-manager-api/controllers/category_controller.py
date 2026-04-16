from flask import request, jsonify
from database import db
from models.category import Category
from models.task import Task


class CategoryController:

    @staticmethod
    def get_all():
        result = []
        for c in Category.query.all():
            data = c.to_dict()
            data['task_count'] = Task.query.filter_by(category_id=c.id).count()
            result.append(data)
        return jsonify(result), 200

    @staticmethod
    def create():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400

        name = data.get('name')
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400

        category = Category(
            name=name,
            description=data.get('description', ''),
            color=data.get('color', '#000000'),
        )

        try:
            db.session.add(category)
            db.session.commit()
            return jsonify(category.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Erro ao criar categoria'}), 500

    @staticmethod
    def update(cat_id):
        cat = db.session.get(Category, cat_id)
        if not cat:
            return jsonify({'error': 'Categoria não encontrada'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400

        if 'name' in data:
            cat.name = data['name']
        if 'description' in data:
            cat.description = data['description']
        if 'color' in data:
            cat.color = data['color']

        try:
            db.session.commit()
            return jsonify(cat.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Erro ao atualizar'}), 500

    @staticmethod
    def delete(cat_id):
        cat = db.session.get(Category, cat_id)
        if not cat:
            return jsonify({'error': 'Categoria não encontrada'}), 404

        try:
            db.session.delete(cat)
            db.session.commit()
            return jsonify({'message': 'Categoria deletada'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Erro ao deletar'}), 500
