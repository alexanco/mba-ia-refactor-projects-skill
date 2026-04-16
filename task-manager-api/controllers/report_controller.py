from flask import jsonify
from database import db
from models.task import Task, _utcnow
from models.user import User
from models.category import Category
from datetime import timedelta
from sqlalchemy import func, case


class ReportController:

    @staticmethod
    def summary():
        total_tasks = Task.query.count()
        total_users = User.query.count()
        total_categories = Category.query.count()

        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()

        priority_counts = dict(
            db.session.query(Task.priority, func.count(Task.id))
            .group_by(Task.priority)
            .all()
        )

        now = _utcnow()
        overdue_count = 0
        overdue_list = []
        for t in Task.query.all():
            if t.is_overdue():
                overdue_count += 1
                overdue_list.append({
                    'id': t.id,
                    'title': t.title,
                    'due_date': str(t.due_date),
                    'days_overdue': (now - t.due_date).days,
                })

        seven_days_ago = now - timedelta(days=7)
        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
        recent_done = Task.query.filter(
            Task.status == 'done',
            Task.updated_at >= seven_days_ago
        ).count()

        # Single GROUP BY query instead of N+1
        user_stats_raw = (
            db.session.query(
                User.id,
                User.name,
                func.count(Task.id).label('total'),
                func.sum(case((Task.status == 'done', 1), else_=0)).label('completed'),
            )
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .all()
        )

        user_stats = [
            {
                'user_id': row.id,
                'user_name': row.name,
                'total_tasks': row.total or 0,
                'completed_tasks': int(row.completed or 0),
                'completion_rate': round((row.completed / row.total) * 100, 2) if row.total else 0,
            }
            for row in user_stats_raw
        ]

        return jsonify({
            'generated_at': str(now),
            'overview': {
                'total_tasks': total_tasks,
                'total_users': total_users,
                'total_categories': total_categories,
            },
            'tasks_by_status': {
                'pending': pending,
                'in_progress': in_progress,
                'done': done,
                'cancelled': cancelled,
            },
            'tasks_by_priority': {
                'critical': priority_counts.get(1, 0),
                'high': priority_counts.get(2, 0),
                'medium': priority_counts.get(3, 0),
                'low': priority_counts.get(4, 0),
                'minimal': priority_counts.get(5, 0),
            },
            'overdue': {
                'count': overdue_count,
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': recent_tasks,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }), 200

    @staticmethod
    def user_report(user_id):
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        tasks = Task.query.filter_by(user_id=user_id).all()
        total = len(tasks)
        done = pending = in_progress = cancelled = overdue = high_priority = 0

        for t in tasks:
            if t.status == 'done':
                done += 1
            elif t.status == 'pending':
                pending += 1
            elif t.status == 'in_progress':
                in_progress += 1
            elif t.status == 'cancelled':
                cancelled += 1
            if t.priority <= 2:
                high_priority += 1
            if t.is_overdue():
                overdue += 1

        return jsonify({
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': pending,
                'in_progress': in_progress,
                'cancelled': cancelled,
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
            },
        }), 200
