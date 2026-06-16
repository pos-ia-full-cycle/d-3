const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcryptjs');

let db;

function getDb() {
    if (!db) db = new sqlite3.Database(':memory:');
    return db;
}

function dbRun(sql, params = []) {
    return new Promise((resolve, reject) => {
        getDb().run(sql, params, function (err) {
            if (err) reject(err);
            else resolve(this);
        });
    });
}

async function initDb() {
    await dbRun('PRAGMA foreign_keys = ON');

    await dbRun(`CREATE TABLE users (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        name  TEXT    NOT NULL,
        email TEXT    UNIQUE NOT NULL,
        pass  TEXT    NOT NULL
    )`);

    await dbRun(`CREATE TABLE courses (
        id     INTEGER PRIMARY KEY AUTOINCREMENT,
        title  TEXT    NOT NULL,
        price  REAL    NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    )`);

    await dbRun(`CREATE TABLE enrollments (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id   INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        FOREIGN KEY (user_id)   REFERENCES users(id)   ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
    )`);

    await dbRun(`CREATE TABLE payments (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment_id INTEGER NOT NULL,
        amount        REAL    NOT NULL,
        status        TEXT    NOT NULL,
        FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE
    )`);

    await dbRun(`CREATE TABLE audit_logs (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        action     TEXT    NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    const passwordHash = await bcrypt.hash('123456', 12);
    await dbRun("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", ['Leonan', 'leonan@fullcycle.com.br', passwordHash]);
    await dbRun("INSERT INTO courses (title, price, active) VALUES (?, ?, ?)", ['Clean Architecture', 997.00, 1]);
    await dbRun("INSERT INTO courses (title, price, active) VALUES (?, ?, ?)", ['Docker', 497.00, 1]);
    await dbRun("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [1, 1]);
    await dbRun("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [1, 997.00, 'PAID']);
}

async function runInTransaction(operations) {
    await dbRun('BEGIN');
    try {
        const result = await operations();
        await dbRun('COMMIT');
        return result;
    } catch (err) {
        await dbRun('ROLLBACK');
        throw err;
    }
}

module.exports = { getDb, initDb, runInTransaction };
