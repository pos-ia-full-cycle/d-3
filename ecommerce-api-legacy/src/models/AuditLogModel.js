const { getDb } = require('../db');

function run(sql, params) {
    return new Promise((resolve, reject) => {
        getDb().run(sql, params, function (err) { err ? reject(err) : resolve(this); });
    });
}

const AuditLogModel = {
    record(action) {
        return run('INSERT INTO audit_logs (action) VALUES (?)', [action]);
    },
};

module.exports = AuditLogModel;
