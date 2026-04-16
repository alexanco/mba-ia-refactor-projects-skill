const Database = require('better-sqlite3');
const bcrypt = require('bcryptjs');
const config = require('./index');

const db = new Database(config.dbPath);

function initDb() {
    db.exec(`
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            pass TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY,
            enrollment_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY,
            action TEXT NOT NULL,
            created_at DATETIME NOT NULL
        );
    `);

    const { count } = db.prepare('SELECT COUNT(*) AS count FROM users').get();
    if (count === 0) {
        const passwordHash = bcrypt.hashSync('123456', 12);
        db.prepare('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)').run('Leonan', 'leonan@fullcycle.com.br', passwordHash);
        db.prepare('INSERT INTO courses (title, price, active) VALUES (?, ?, ?)').run('Clean Architecture', 997.00, 1);
        db.prepare('INSERT INTO courses (title, price, active) VALUES (?, ?, ?)').run('Docker', 497.00, 1);
        db.prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)').run(1, 1);
        db.prepare('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)').run(1, 997.00, 'PAID');
    }
}

module.exports = { db, initDb };
