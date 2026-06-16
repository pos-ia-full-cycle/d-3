const ReportModel = require('../models/ReportModel');

const ReportService = {
    async getFinancialReport() {
        const rows = await ReportModel.getEnrollmentDetails();

        const courseMap = new Map();

        for (const row of rows) {
            if (!courseMap.has(row.course_id)) {
                courseMap.set(row.course_id, { course: row.title, revenue: 0, students: [] });
            }

            const courseData = courseMap.get(row.course_id);

            if (row.student_name) {
                if (row.status === 'PAID') courseData.revenue += row.amount;
                courseData.students.push({
                    student: row.student_name,
                    paid: row.amount ?? 0,
                });
            }
        }

        return Array.from(courseMap.values());
    },
};

module.exports = ReportService;
