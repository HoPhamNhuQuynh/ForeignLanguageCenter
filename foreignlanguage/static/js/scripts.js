    console.log("SCRIPT LOADED");


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
//rollcall
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

//enterscore
function updateDTB() {
    const row = this.closest('tr');
    const inputs = row.querySelectorAll('.score-input');
    let total = 0;
    let weightSum = 0;

    inputs.forEach(input => {
        let val = parseFloat(input.value);
        if (!isNaN(val) && val >= 0) {
            total += val * parseFloat(input.dataset.weight);
            weightSum += parseFloat(input.dataset.weight);
        } else if (val < 0) {
            input.value = 0; // Không cho âm
        }
    });

    const dtb = weightSum > 0 ? (total / weightSum) : 0;
    row.querySelector('.dtb').textContent = dtb.toFixed(2);
    row.querySelector('.result').textContent = dtb >=5 ? "Đậu" : "Rớt";

    let rank = '';
    if (dtb >=8) rank = "Giỏi";
    else if (dtb >=6.5) rank = "Khá";
    else if (dtb >=5) rank = "Trung bình";
    else rank = "Yếu";
    row.querySelector('.rank').textContent = rank;
}

// Gắn blur cho tất cả input khi load trang
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.score-input').forEach(input => {
        input.addEventListener('blur', updateDTB);
    });
});

