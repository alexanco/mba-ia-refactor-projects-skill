const { db } = require('../config/database');

class AuditLogModel {
    static create(action) {
        db.prepare("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))").run(action);
    }
}

module.exports = AuditLogModel;
