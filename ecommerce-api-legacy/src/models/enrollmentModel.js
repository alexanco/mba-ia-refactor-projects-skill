const { db } = require('../config/database');

class EnrollmentModel {
    static create({ userId, courseId }) {
        const result = db.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)').run(userId, courseId);
        return result.lastInsertRowid;
    }
}

module.exports = EnrollmentModel;
