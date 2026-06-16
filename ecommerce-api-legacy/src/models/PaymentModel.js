const { getDb } = require('../db');

function run(sql, params) {
    return new Promise((resolve, reject) => {
        getDb().run(sql, params, function (err) { err ? reject(err) : resolve(this); });
    });
}

const PaymentModel = {
    async create(enrollmentId, amount, status) {
        const result = await run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]
        );
        return result.lastID;
    },
};

module.exports = PaymentModel;
