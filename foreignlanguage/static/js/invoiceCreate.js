window.resetForm = function() {
    const form = document.getElementById('invoiceForm');
    if (form) form.reset();
    
    const btnSubmit = document.getElementById('btnSubmit');
    const btnDelete = document.getElementById('btnDelete');
    if (btnSubmit) btnSubmit.disabled = true;
    if (btnDelete) btnDelete.disabled = true;
    
    document.querySelectorAll('.student-row').forEach(r => r.classList.remove('row-active'));
}

window.selectRow = function(row, id, name, course, actualTuition, debt) {
    document.querySelectorAll('.student-row').forEach(r => r.classList.remove('row-active'));
    row.classList.add('row-active');

    document.getElementById('inp_regis_id').value = id;
    document.getElementById('inp_name').value = name;
    document.getElementById('inp_course').value = course;
    document.getElementById('inp_content').value = "Thu học phí: " + course;

    const inpAmount = document.getElementById('inp_amount');
    if(inpAmount) inpAmount.value = debt;
    
    document.getElementById('btnDelete').disabled = false;
    document.getElementById('btnSubmit').disabled = false;
}

window.addAlertDel = function(){
    return confirm('CẢNH BÁO: Bạn có chắc chắn muốn XÓA bản đăng ký này? Hành động này không thể hoàn tác.');
}

document.addEventListener('DOMContentLoaded', function() {

    const courseSel  = document.getElementById('modalCourseSelect');
    const levelSel   = document.getElementById('modalLevelSelect');
    const studentSel = document.getElementById('modalStudentSelect');

    if(courseSel) {
        courseSel.addEventListener('change', function() {
            loadLevels(this.value);
        });
    }

    if(levelSel) {
        levelSel.addEventListener('change', function() {
            triggerLoad();
        });
    }

    function triggerLoad() {
        const c_id = courseSel.value;
        const l_id = levelSel.value;
        const s_id = studentSel.value;

        if (c_id && l_id) {
             loadClasses(c_id, l_id, s_id);
        }
    }

    function renderClassesTable(data){
        const tableBodyClasses = document.getElementById("tableBodyClasses");

        tableBodyClasses.innerHTML = "";

        if (!data || data.length === 0) {
             tableBodyClasses.innerHTML = '<tr><td colspan="4" class="text-danger text-center py-3">Không có lớp phù hợp (hoặc học viên đã học).</td></tr>';
            return;
        }

        data.forEach(c => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <input type="radio" name="class_id" value="${c.id}" required style="transform: scale(1.2);">
                </td>
                <td class="fw-bold">Lớp ${c.id}</td>
                <td class="startTime">${c.start_time}</td>
                <td><span class="badge bg-light text-dark border">${c.current_count}/${c.maximum_stu}</span></td>`;
            tableBodyClasses.appendChild(tr);
        });
    }

    function loadClasses(c_id, l_id, stu_id){
        fetch(`api/classes?course_id=${c_id}&level_id=${l_id}&student_id=${stu_id}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(res => res.json())
        .then(data => {
            renderClassesTable(data);
        })
        .catch(err => {
            console.error("Lỗi tải lớp:", err);
        });
    }

    function loadLevels(course_id) {
        if (!course_id) return;
        const levelSelect = document.getElementById("modalLevelSelect");

        fetch(`/api/level?course_id=${course_id}`)
            .then(res => res.json())
            .then(data => {
                levelSelect.innerHTML = '<option selected disabled value="">-- Chọn cấp độ --</option>';

                data.forEach(level => {
                    const option = document.createElement("option");
                    option.value = level.id;
                    option.textContent = level.name;
                    levelSelect.appendChild(option);
                });
            });
    }
});