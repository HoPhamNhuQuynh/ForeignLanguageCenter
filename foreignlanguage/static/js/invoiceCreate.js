    const fmt = new Intl.NumberFormat('vi-VN');

    function resetForm() {
        document.getElementById('invoiceForm').reset();
        document.getElementById('btnSubmit').disabled = true;
        document.querySelectorAll('.student-row').forEach(r => r.classList.remove('row-active'));

        // Reset hiển thị
        document.getElementById('display_amount_text').value = "0 ₫";
        document.getElementById('inp_amount_hidden').value = "";
        document.getElementById('lbl_full_amount').innerText = "0 ₫";
        document.getElementById('lbl_half_amount').innerText = "0 ₫";

        // Reset thẻ card
        toggleCardState('card_full', false);
        toggleCardState('card_half', false);
        document.getElementById('opt_full').disabled = true;
        document.getElementById('opt_half').disabled = true;
    }

    function toggleCardState(cardId, enabled) {
        const card = document.getElementById(cardId);
        if (enabled) {
            card.classList.remove('disabled');
        } else {
            card.classList.add('disabled');
        }
    }

    function updateAmount(value) {
        document.getElementById('inp_amount_hidden').value = value;
        document.getElementById('display_amount_text').value = fmt.format(value) + " ₫";
    }

function selectRow(row, id, name, course, actualTuition, debt) {
    // Highlight active row
    document.querySelectorAll('.student-row').forEach(r => r.classList.remove('row-active'));
    row.classList.add('row-active');

    // Fill Form Info
    document.getElementById('inp_regis_id').value = id;
    document.getElementById('inp_name').value = name;
    document.getElementById('inp_course').value = course;
    document.getElementById('inp_content').value = "Thu học phí: " + course;

    // 👉 DÒNG QUAN TRỌNG BỊ THIẾU
    document.getElementById('inp_amount').value = debt;
    document.getElementById('btnDelete').disabled = false;
    document.getElementById('btnSubmit').disabled = false;
}

