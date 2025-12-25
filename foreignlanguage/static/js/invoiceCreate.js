//Form
const fmt = new Intl.NumberFormat('vi-VN');

function resetForm() {
    document.getElementById('invoiceForm').reset();
    document.getElementById('btnSubmit').disabled = true;
    document.getElementById('btnDelete').disabled = true;
    document.querySelectorAll('.student-row').forEach(r => r.classList.remove('row-active'));
}

function selectRow(row, id, name, course, actualTuition, debt) {
    document.querySelectorAll('.student-row').forEach(r => r.classList.remove('row-active'));
    row.classList.add('row-active');

    document.getElementById('inp_regis_id').value = id;
    document.getElementById('inp_name').value = name;
    document.getElementById('inp_course').value = course;
    document.getElementById('inp_content').value = "Thu học phí: " + course;

    document.getElementById('inp_amount').value = debt;
    document.getElementById('btnDelete').disabled = false;
    document.getElementById('btnSubmit').disabled = false;
}

function addAlertDel(){
    return confirm('CẢNH BÁO: Bạn có chắc chắn muốn XÓA bản đăng ký này? Hành động này không thể hoàn tác.');
}



