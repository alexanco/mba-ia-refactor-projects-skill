const { db } = require('../config/database');

class UserModel {
    static findByEmail(email) {
        return db.prepare('SELECT id, name, email FROM users WHERE email = ?').get(email);
    }

    static findById(id) {
        return db.prepare('SELECT id, name, email FROM users WHERE id = ?').get(id);
    }

    static create({ name, email, passwordHash }) {
        const result = db.prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)').run(name, email, passwordHash);
        return result.lastInsertRowid;
    }

    static deleteById(id) {
        return db.prepare('DELETE FROM users WHERE id = ?').run(id);
    }
}

module.exports = UserModel;
