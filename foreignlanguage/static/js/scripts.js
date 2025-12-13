    function togglePass(inputId, icon) {
        const input = document.getElementById(inputId);
        const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
        input.setAttribute('type', type);

        // Đổi icon
        if (type === 'text') {
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        } else {
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        }
    }

    document.addEventListener("DOMContentLoaded", function() {
    const currentPath = window.location.pathname;

    const navLinks = document.querySelectorAll('.navbar-nav .nav-link, .navbar-nav .dropdown-item ');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');

        if (href === currentPath) {
            link.classList.add('active');

            if(link.classList.contains('dropdown-item')){
                link.closest('.dropdown').querySelector('.nav-link.dropdown-toggle').classList.add('active');
            }
        }
    });
});

//-------TEACHER------------
document.getElementById('classSelect').addEventListener('change', function () {
    const classId = this.value;
    if (!classId) return;

    fetch(`./load-by-class?class_id=${classId}`)
        .then(res => res.json())
        .then(data => {
            // Buổi học
            const sessionSelect = document.getElementById('sessionSelect');
            sessionSelect.innerHTML = '<option value="">-- Chọn buổi học --</option>';
            data.sessions.forEach(s => {
                sessionSelect.innerHTML +=
                    `<option value="${s.id}">${s.name}</option>`;
            });

            // Học viên
            const tbody = document.getElementById('studentBody');
            tbody.innerHTML = '';
            data.students.forEach((stu, index) => {
                tbody.innerHTML += `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${stu.name}</td>
                        <td>
                            <input type="radio" name="${stu.id}" value="1"> Có mặt
                            <input type="radio" name="${stu.id}" value="0" class="ms-3"> Vắng
                        </td>
                    </tr>
                `;
            });
        });
});
