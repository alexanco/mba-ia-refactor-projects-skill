const { db } = require('../config/database');
const { PAYMENT_STATUS } = require('./paymentService');

class ReportService {
    static getFinancialReport() {
        const rows = db.prepare(`
            SELECT
                c.id       AS course_id,
                c.title    AS course_title,
                u.name     AS student_name,
                p.amount   AS paid_amount,
                p.status   AS payment_status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u       ON u.id = e.user_id
            LEFT JOIN payments p    ON p.enrollment_id = e.id
            ORDER BY c.id
        `).all();

        const reportMap = {};
        for (const row of rows) {
            if (!reportMap[row.course_id]) {
                reportMap[row.course_id] = {
                    course: row.course_title,
                    revenue: 0,
                    students: [],
                };
            }

            if (row.student_name) {
                reportMap[row.course_id].students.push({
                    student: row.student_name,
                    paid: row.paid_amount || 0,
                });

                if (row.payment_status === PAYMENT_STATUS.PAID) {
                    reportMap[row.course_id].revenue += row.paid_amount;
                }
            }
        }

        return Object.values(reportMap);
    }
}

module.exports = ReportService;
