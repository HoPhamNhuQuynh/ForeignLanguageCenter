   // rollcall
  document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.getElementById('classSelect');
    const saveBtn = document.getElementById('saveBtn');
    const sessionSelect = document.getElementById('sessionSelect');
    const tbody = document.getElementById('studentBody');

    function checkCompletion() {
        const radios = document.querySelectorAll('.attendance-check');

        const names = new Set();
        radios.forEach(r => names.add(r.name));
        const totalStudents = names.size;

        const checkedCount = document.querySelectorAll('.attendance-check:checked').length;

        if (totalStudents > 0 && checkedCount === totalStudents) {
            saveBtn.classList.remove('d-none');
        } else {
            saveBtn.classList.add('d-none');
        }
    }
    if (classSelect){
        classSelect.addEventListener('change', () => {
        const classId = classSelect.value;
        if (!classId) return;

        if (saveBtn) saveBtn.classList.add('d-none');

        fetch('/admin/rollcall/api/load-by-class?class_id=' + classId)
            .then(res => res.json())
            .then(data => {
                if (sessionSelect) {
                    sessionSelect.innerHTML = '<option value="">-- Chọn buổi học --</option>';
                    if (data.sessions) {
                        data.sessions.forEach(s => {
                        sessionSelect.innerHTML += `<option value="${s.id}">${s.name}</option>`;
                        });
                    }
                }

                if (studentBody) {
                    studentBody.innerHTML = '';
                        if (data.students) {
                            data.students.forEach((stu, i) => {
                                studentBody.innerHTML += `
                                    <tr>
                                        <td>${i + 1}</td>
                                        <td class="text-start ps-4 fw-bold">${stu.name}</td>
                                        <td>
                                            <input type="radio" class="attendance-check" name="student_${stu.id}" value="1"> Có mặt
                                            <input type="radio" class="attendance-check ms-3" name="student_${stu.id}" value="0"> Vắng
                                        </td>
                                    </tr>
                                `;
                            });
                        }
                    }
                })
                .catch(err => console.error(err));
            });
    }

    if (sessionSelect) {
        sessionSelect.addEventListener('change', function() {
            const sessionId = this.value;
            if (!sessionId) return;

            document.querySelectorAll('.attendance-check').forEach(r => r.checked = false);
            if (saveBtn) saveBtn.classList.add('d-none');

            fetch(`/admin/rollcall/api/get-attendance?session_id=${sessionId}`)
                .then(res => res.json())
                .then(data => {
                    const attendance = data.attendance || {}; // { "1": 1, "2": 0 }

                    document.querySelectorAll('.attendance-check').forEach(radio => {
                        const studentId = radio.name.replace('student_', '');
                        const status = attendance[studentId];

                        if (status !== undefined) {
                            if (radio.value == status) {
                                radio.checked = true; // Tự động tick
                            }
                        }
                    });

                    checkCompletion();
                })
                .catch(err => console.error("Lỗi load điểm danh:", err));
        });
    }

    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('attendance-check')) {
            checkCompletion();
        }
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

        const hiddenDTB = row.querySelector('.hidden-dtb');
        const hiddenStatus = row.querySelector('.hidden-status');

        if (hiddenDTB) hiddenDTB.value = dtb.toFixed(2);
        if (hiddenStatus) hiddenStatus.value = dtb >= 5 ? "PASSED" : "FAILED";
    }

    document.addEventListener('DOMContentLoaded', function() {

        loadScoreDraft();

        // Lắng nghe tất cả các ô nhập điểm
        const scoreInputs = document.querySelectorAll('input[name^="score_"]');
        scoreInputs.forEach(input => {
            // Giữ nguyên sự kiện blur cũ của bạn
            input.addEventListener('blur', updateDTB);

            input.addEventListener('input', function() {
                saveScoreDraft(this);
                updateDTB.call(this);
            });
        });

        if (document.querySelector('.alert-success')) {
            clearScoreDraft();
        }
    });

    function saveScoreDraft(inputElement) {
        const val = inputElement.value;
        let draft = JSON.parse(localStorage.getItem('teacher_score_draft')) || {};
        draft[inputElement.name] = val;
        localStorage.setItem('teacher_score_draft', JSON.stringify(draft));
    }

    // 2. Hàm khôi phục dữ liệu khi trang web load lại
    function loadScoreDraft() {
        let draft = JSON.parse(localStorage.getItem('teacher_score_draft'));
        if (!draft) return;

        Object.keys(draft).forEach(scoreId => {
            let input = document.querySelector(`input[name="${scoreId}"]`);
            if (input) {
                input.value = draft[scoreId];
                updateDTB.call(input);
            }
        });
    }

    function clearScoreDraft() {
        localStorage.removeItem('teacher_score_draft');
    }
});
