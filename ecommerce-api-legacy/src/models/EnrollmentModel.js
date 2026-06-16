const { getDb } = require('../db');

function run(sql, params) {
    return new Promise((resolve, reject) => {
        getDb().run(sql, params, function (err) { err ? reject(err) : resolve(this); });
    });
}

const EnrollmentModel = {
    async create(userId, courseId) {
        const result = await run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId]
        );
        return result.lastID;
    },
};

module.exports = EnrollmentModel;
