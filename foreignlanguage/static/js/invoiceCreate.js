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

        // Logic 50%
        let halfTuition = actualTuition / 2;

        // --- Option Full ---
        let optFull = document.getElementById('opt_full');
        toggleCardState('card_full', true);
        optFull.disabled = false;
        optFull.value = debt;
        optFull.checked = true; // Mặc định chọn Full
        document.getElementById('lbl_full_amount').innerText = fmt.format(debt) + " ₫";

        // --- Option Half ---
        let optHalf = document.getElementById('opt_half');
        // Logic: Nợ > 50% (+1000đ sai số) nghĩa là chưa đóng lần đầu
        if (debt > halfTuition + 1000) {
            toggleCardState('card_half', true);
            optHalf.disabled = false;
            optHalf.value = halfTuition;
            document.getElementById('lbl_half_amount').innerText = fmt.format(halfTuition) + " ₫";
        } else {
            toggleCardState('card_half', false);
            optHalf.disabled = true;
            document.getElementById('lbl_half_amount').innerText = "Đã hoàn thành";
        }

        // Update Total display
        updateAmount(debt);
        document.getElementById('btnSubmit').disabled = false;
    }