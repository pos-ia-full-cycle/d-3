const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const currentLevel = LEVELS[process.env.LOG_LEVEL] ?? LEVELS.info;

function log(level, message) {
    if (LEVELS[level] <= currentLevel) {
        const output = `[${new Date().toISOString()}] [${level.toUpperCase()}] ${message}`;
        level === 'error' ? console.error(output) : console.log(output);
    }
}

module.exports = {
    error: (msg) => log('error', msg),
    warn:  (msg) => log('warn', msg),
    info:  (msg) => log('info', msg),
    debug: (msg) => log('debug', msg),
};
