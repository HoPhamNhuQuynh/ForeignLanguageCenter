    document.getElementById('regulationForm').addEventListener('submit', function(e) {
        const inputs = document.querySelectorAll('.tuition-input');
        let hasChange = false;
        let hasError = false;

        inputs.forEach(input => {
            const currentVal = parseFloat(input.value);
            const originalVal = parseFloat(input.getAttribute('data-original'));

            if (!currentVal || currentVal <= 0) {
                hasError = true;
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }

            if (currentVal !== originalVal) {
                hasChange = true;
            }
        });

        if (hasError) {
            e.preventDefault();
            alert("Vui lòng nhập học phí hợp lệ (lớn hơn 0)!");
            return;
        }

        if (!hasChange) {
            e.preventDefault();
            alert("Bạn chưa thay đổi mức học phí nào cả!");
            return;
        }
    });