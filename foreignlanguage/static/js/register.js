document.addEventListener("DOMContentLoaded", function() {
    initRegisterFromCourse();
    document.querySelector('input[name="payment_method"][value="2"]').checked = true;
});

// truyen tham so tu course qua register-course
    function initRegisterFromCourse(){
        let c = document.getElementById("courseSelect")
        let l = document.getElementById("levelSelect")
        if (!c || !l) return;

        const params = new URLSearchParams(window.location.search);
        let c_id = params.get("course_id")
        let l_id = params.get("level_id")

        if (c_id && l_id){
            c.value = c_id
            l.value = l_id
            loadClasses(c_id, l_id)
        }
    }

    // cap nhat duong dan moi khi thay doi selectbox
    function updateFromSelect(){
        const c = document.getElementById("courseSelect")
        const l = document.getElementById("levelSelect")
        let c_id = c.value
        let l_id = l.value
        if (!c_id || !l_id) return;

        history.replaceState(null, "", `${window.location.pathname}?course_id=${c_id}&level_id=${l_id}`)

    }

    // gan su kien
    document.getElementById("courseSelect").addEventListener('change', function() {
        loadClasses(this.value, document.getElementById('levelSelect').value);
        updateFromSelect();
    });

    document.getElementById("levelSelect").addEventListener('change', function() {
        loadClasses(document.getElementById('courseSelect').value, this.value);
        updateFromSelect();
    });

    function renderClassesTable(data){
        const tableBodyClasses = document.getElementById("tableBodyClasses");
        const tableClasses = document.getElementById("tableClasses");
        const tableInform = document.getElementById("tableInform");

        tableBodyClasses.innerHTML = "";

        if (!data || data.length === 0) {
            tableClasses.classList.add("d-none");
            tableInform.classList.remove("d-none");
            return;
        }

        tableInform.classList.add("d-none");
        tableClasses.classList.remove("d-none");

        data.forEach(c => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <input type="radio" name="class_id" value="${c.id}">
                </td>
                <td>${c.id}</td>
                <td class="startTime">${c.start_time}</td>
                <td>${c.current_count}/${c.maximum_stu}</td>`;
            tableBodyClasses.appendChild(tr);
        });
    }


    function loadClasses(c_id, l_id){
        if (!c_id || !l_id) return;
        fetch(`api/classes?course_id=${c_id}&level_id=${l_id}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(res=>res.json()).then(data=>{
            renderClassesTable(data);
        });
    }

    // bat su kien load hoa don khi chon radio lop hoc
    document.getElementById("tableBodyClasses").addEventListener('change', function(e) {
        if (e.target && e.target.type === 'radio'){
            const r = e.target
            const courseSelect = document.getElementById("courseSelect");
            const levelSelect = document.getElementById("levelSelect");

            document.getElementById('courseName').textContent = courseSelect.options[courseSelect.selectedIndex].text;
            document.getElementById('levelName').textContent = levelSelect.options[levelSelect.selectedIndex].text;
            document.getElementById('classId').textContent = r.value;

            const tr = r.closest("tr");
            document.getElementById('startTime').textContent = tr.querySelector(".startTime").innerText;

            const method_label = document.querySelector('input[name="payment_method"]:checked').closest("label");
            document.getElementById('methodPay').textContent = method_label.querySelector(".methodName").innerText;

            const percent_label = document.querySelector('input[name="payment_percent"]:checked').closest("label");
            document.getElementById('percentPay').textContent = percent_label.querySelector(".percentName").innerText;

            console.log(r.value)
            loadInvoice(r.value);
        }

    });

    // cap nhat phuong thuc len hoa don
    document.querySelector(".list-group").addEventListener("change", function (e) {
        if (e.target && e.target.type === "radio") {
            const label = e.target.closest("label");
            const methodName = label.querySelector(".methodName").innerText;

            document.getElementById("methodPay").textContent = methodName;
        }
    });

    // cap nhap muc thanh toan len hoa don
    document.querySelector(".list-percent").addEventListener("change", function (e) {
        if (e.target && e.target.type === "radio" && e.target.name === "payment_percent") {
            document.querySelectorAll(".payment-option")
                .forEach(lb => lb.classList.remove("selected-option"));
            const label = e.target.closest(".payment-option");
            label.classList.add("selected-option");
            const percent = e.target.value;

            const percentName = label.querySelector(".percentName").innerText;
            console.log(percent, percentName);

            document.getElementById("percentPay").textContent = percentName;

            const classRadio = document.querySelector('input[name="class_id"]:checked');
            if (classRadio) {
                loadInvoice(classRadio.value);
            }
        }
    });

    function loadInvoice(class_id){
        fetch(`api/tuition?class_id=${class_id}`, {
            method: 'get',
            headers: {
                'Content-Type': 'application/json'
            }}).then(res=>res.json()).then(data=>{
                const percentInput = document.querySelector('input[name="payment_percent"]:checked')
                const percent = percentInput ? percentInput.value : '100';

                let tuition = data.tuition;
                if (percent === '50') {
                    tuition = Math.ceil(tuition / 2);
                }
                document.getElementById('totalPrice').textContent = tuition.toLocaleString() + ' VND';
        });
    }

    // xu ly nut dang ky
    const btnRegister = document.getElementById("btnRegister")
    btnRegister.addEventListener('click', function() {
        const name = document.getElementById("name").value
        const phone_num = document.getElementById("phone_num").value
        const class_id = document.querySelector('input[name="class_id"]:checked').value
        const payment_method = document.querySelector('input[name="payment_method"]:checked').value

        const payment_percent = document.querySelector('input[name="payment_percent"]:checked').value
        const totalPriceText = document.getElementById("totalPrice").innerText;
        let tuition = parseFloat(totalPriceText.replace(/,/g, '').replace(' VND',''));


        console.log(payment_method)
        console.log(payment_percent)
        addRegistration(name, phone_num, class_id, payment_method, payment_percent, tuition);
    });

    function addRegistration(name, phone_num, class_id, payment_method, payment_percent, tuition){
        if (!name || !phone_num || !class_id || !payment_method || !payment_percent)
            {
                alert("Vui lòng nhập đầy đủ thông tin trước khi nhấn nút đăng ký!")
                return;
            }

        if (confirm("Bạn có chắc chắc muốn đăng ký khóa học và thanh toán ngay?")===true){
            fetch("api/registrations", {
                method: "post",
                body: JSON.stringify({
                    "name": name,
                    "phone": phone_num,
                    "class_id": class_id,
                    "payment_method": parseInt(payment_method),
                    "payment_percent": payment_percent,
                    "money": tuition
                }),
                headers: {
                    "Content-type": "application/json"
                }
            }).then(res=>res.json()).then(data=>{
                alert(data.msg);
                if (data.success) {
                    location.reload();
                }
                console.log(data)
            })
        }
    }

