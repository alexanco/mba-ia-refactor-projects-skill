const { db } = require('../config/database');

class CourseModel {
    static findActiveById(id) {
        return db.prepare('SELECT * FROM courses WHERE id = ? AND active = 1').get(id);
    }
}

module.exports = CourseModel;
