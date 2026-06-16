const { getDb } = require('../db');

function get(sql, params) {
    return new Promise((resolve, reject) => {
        getDb().get(sql, params, (err, row) => (err ? reject(err) : resolve(row || null)));
    });
}

const CourseModel = {
    findActiveById(id) {
        return get('SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [id]);
    },
};

module.exports = CourseModel;
