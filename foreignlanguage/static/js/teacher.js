
   // rollcall
  document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.getElementById('classSelect');
    const saveBtn = document.getElementById('saveBtn');

    classSelect.addEventListener('change', () => {
        const classId = classSelect.value;
        if (!classId) return;

        fetch('load-by-class?class_id=' + classId)
            .then(res => res.json())
            .then(data => {
                // sessions
                const sessionSelect = document.getElementById('sessionSelect');
                sessionSelect.innerHTML = '<option value="">-- Chọn buổi học --</option>';
                data.sessions.forEach(s => {
                    sessionSelect.innerHTML += `<option value="${s.id}">${s.name}</option>`;
                });

                // students
                const tbody = document.getElementById('studentBody');
                tbody.innerHTML = '';
                data.students.forEach((stu, i) => {
                    tbody.innerHTML += `
                        <tr>
                            <td>${i + 1}</td>
                            <td>${stu.name}</td>
                            <td>
                                <input type="radio" name="student_${stu.id}" value="1"> Có mặt
                                <input type="radio" name="student_${stu.id}" value="0"> Vắng
                            </td>
                        </tr>
                    `;
                });
            });
    });

    document.addEventListener('change', () => {
        const radios = document.querySelectorAll('#studentBody input[type="radio"]');
        const checked = new Set([...radios].filter(r => r.checked).map(r => r.name));
        saveBtn.classList.toggle('d-none', checked.size * 2 !== radios.length);
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

