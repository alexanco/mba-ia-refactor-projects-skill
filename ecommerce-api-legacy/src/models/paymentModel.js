const { db } = require('../config/database');

class PaymentModel {
    static create({ enrollmentId, amount, status }) {
        const result = db.prepare('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)').run(enrollmentId, amount, status);
        return result.lastInsertRowid;
    }
}

module.exports = PaymentModel;
