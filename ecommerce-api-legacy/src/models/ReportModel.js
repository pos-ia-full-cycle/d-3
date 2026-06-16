const { getDb } = require('../db');

function all(sql, params) {
    return new Promise((resolve, reject) => {
        getDb().all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
}

const ReportModel = {
    getEnrollmentDetails() {
        return all(`
            SELECT
                c.id   AS course_id,
                c.title,
                u.name AS student_name,
                p.amount,
                p.status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users      u ON u.id = e.user_id
            LEFT JOIN payments   p ON p.enrollment_id = e.id
            ORDER BY c.id
        `, []);
    },
};

module.exports = ReportModel;
