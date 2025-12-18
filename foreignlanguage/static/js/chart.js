export function initCharts(data){
    const { ratioPassedLabels, ratioPassedData, revenueLabels, revenueData,
       studentLabels, studentData, topCourseLabels, topCourseData } = data

    Chart.defaults.font.family = "'Segoe UI', sans-serif";
    Chart.defaults.color = '#8898aa';

    function getChartTitle(text) {
        return {
            display: true,
            text: text,
            align: 'start',
            color: '#334455',
            font: { size: 16, weight: 'bold' },
            padding: { bottom: 20 }
        };
    }

    // line chart doanh thu
    const ctxRevenue = document.getElementById("chartRevenue");
    new Chart(ctxRevenue, {
        type: 'line',
        data: {
            labels: revenueLabels,
            datasets: [{
                label: 'Doanh thu (VND)',
                data: revenueData,
                borderColor: '#5e72e4',
                backgroundColor: 'rgba(94, 114, 228, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            scales: { y: { grid: { borderDash: [2, 2] } } },
            plugins: { title: getChartTitle('DOANH THU THEO THÁNG'), legend: { display: true } }
        }
    });

    // donut chart so luong hoc vien
    const ctxStudent = document.getElementById("chartStudentDist");
    new Chart(ctxStudent, {
        type: 'doughnut',
        data: {
            labels: studentLabels,
            datasets: [{
                data: studentData,
                backgroundColor: ['#5e72e4', '#2dce89', '#11cdef', '#f3a4b5', '#2dce89', '#f5365c', '#5e72e4', '#11cdef', '#fb6340'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '50%',
            plugins: { title: getChartTitle('PHÂN BỔ HỌC VIÊN THEO KHÓA HỌC'), legend: { position: 'bottom' } }
        }
    });

    // bar chart ty le dat theo khoa hoc
    new Chart(document.getElementById("chartPassRate"), {
        type: 'bar',
        data: {
            labels: ratioPassedLabels,
            datasets: [{
                label: 'Tỷ lệ đạt (%)',
                data: ratioPassedData,
                backgroundColor: '#11cdef',
                borderRadius: 5
            }]
        },
        options: {
            plugins: {
                title: getChartTitle('TỶ LỆ ĐẠT THEO KHÓA HỌC'),
                legend: { display: false }
            },
            scales: { x: { grid: { display: false } } }
        }
    });

    // horizontal chart top 3 khoa hoc noi bat
    const ctxTopCourses = document.getElementById("chartTopCourses");
    new Chart(ctxTopCourses, {
        type: 'bar',
        data: {
            labels: topCourseLabels,
            datasets: [{
                label: 'Số học viên đăng ký',
                data: topCourseData,
                backgroundColor: '#ff7f50',
                borderRadius: 5
            }]
        },
        options: {
            indexAxis: 'y',
            plugins: {
                title: {
                    display: true,
                    text: 'TOP 3 KHÓA HỌC NỔI BẬT',
                    font: { size: 16, weight: 'bold' },
                    padding: { bottom: 20 }
                },
                legend: { display: false }
            },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { display: false } }
            }
        }
    });


}