const { getDb } = require('../db');

function get(sql, params) {
    return new Promise((resolve, reject) => {
        getDb().get(sql, params, (err, row) => (err ? reject(err) : resolve(row || null)));
    });
}

function run(sql, params) {
    return new Promise((resolve, reject) => {
        getDb().run(sql, params, function (err) { err ? reject(err) : resolve(this); });
    });
}

const UserModel = {
    findByEmail(email) {
        return get('SELECT id, name, email, pass FROM users WHERE email = ?', [email]);
    },

    findById(id) {
        return get('SELECT id, name, email FROM users WHERE id = ?', [id]);
    },

    async create(name, email, passwordHash) {
        const result = await run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash]
        );
        return result.lastID;
    },

    deleteById(id) {
        return run('DELETE FROM users WHERE id = ?', [id]);
    },
};

module.exports = UserModel;
