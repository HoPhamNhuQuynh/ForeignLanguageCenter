
    document.addEventListener("DOMContentLoaded", function() {
        const e = document.querySelector('input[name="payment_method"][value="2"]')
        e.checked = true
        highlightMenu();
        initRegisterFromCourse();

    });
    console.log("SCRIPT LOADED");


    function togglePass(inputId, icon) {
        const input = document.getElementById(inputId);
        const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
        input.setAttribute('type', type);

        if (type === 'text') {
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        } else {
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        }
    }

    function highlightMenu(){
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
    }

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

    function updateFromSelect(){
        const c = document.getElementById("courseSelect")
        const l = document.getElementById("levelSelect")
        let c_id = c.value
        let l_id = l.value
        if (!c_id || !l_id) return;

        history.replaceState(null, "", `${window.location.pathname}?course_id=${c_id}&level_id=${l_id}`)

    }

    document.getElementById("courseSelect").addEventListener('change', function() {
        loadClasses(this.value, document.getElementById('levelSelect').value);
        updateFromSelect();
    });

    document.getElementById("levelSelect").addEventListener('change', function() {
        loadClasses(document.getElementById('courseSelect').value, this.value);
        updateFromSelect();
    });

    function renderClassesTable(data){
        let tableBodyClasses = document.getElementById("tableBodyClasses")
        let tableClasses = document.getElementById("tableClasses")
        let tableInform = document.getElementById("tableInform")

        tableBodyClasses.innerHTML = "";

            if (!data || data.length === 0) {
                table.classList.add("d-none");
                msg.classList.remove("d-none");
                return;
            }

            msg.classList.add("d-none");
            table.classList.remove("d-none");

            data.forEach(c=>{
                let tr =document.createElement('tr');
                tr.id = `class${c.id}`
                tr.innerHTML = `
                <td>
                    <input
                    type="radio"
                    name="class_id"
                    value="${c.id}">
                </td>
                <td>${ c.id }</td>
                <td class="startTime">${ c.start_time }</td>
                <td>${ c.maximum_stub}</td>
                <td>${ c.current_count }</td>`;

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

    document.getElementById("tableBodyClasses").addEventListener('change', function(e) {
        if (e.target && e.target.type === 'radio'){
            const r = e.target
            const courseSelect = document.getElementById("courseSelect");
            const levelSelect = document.getElementById("levelSelect");

            document.getElementById('courseName').textContent = courseSelect.options[courseSelect.selectedIndex].text;
            document.getElementById('levelName').textContent = levelSelect.options[levelSelect.selectedIndex].text;
            document.getElementById('classId').textContent = r.value;

            // Lấy startTime từ tr chứa radio
            const tr = r.closest("tr");
            document.getElementById('startTime').textContent = tr.querySelector(".startTime").innerText;

            // Lấy phương thức thanh toán
            const method_label = document.querySelector('input[name="payment_method"]:checked').closest("label");
            document.getElementById('methodPay').textContent = method_label.querySelector(".methodName").innerText;

            // Lấy phần trăm thanh toán
            const percent_label = document.querySelector('input[name="payment_percent"]:checked').closest("label");
            document.getElementById('percentPay').textContent = percent_label.querySelector(".percentName").innerText;

            // Load hóa đơn
            loadInvoice(r.value);
        }

    });


    function loadInvoice(class_id){
        fetch(`api/tuition?${class_id}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }}).then(res=>res.json()).then(data=>{
                document.getElementById('totalPrice').textContent = data.tuition.toLocaleString() + 'VND'
            });

    }

    const btnRegister = document.getElementById("btnRegister")
    btnRegister.addEventListener('click', function() {
        const name = document.getElementById("name").value
        const phone_num = document.getElementById("phone_num").value
        const class_id = document.querySelector('input[name="class_id"]:checked').value
        const payment_method = document.querySelector('input[name="payment_method"]:checked').value
        const payment_percent = document.querySelector('input[name="payment_percent"]:checked').value

        addRegistration(name, phone_num, class_id, payment_method, payment_percent);
    });

    function addRegistration(name, phone_num, class_id, payment_method, payment_percent){
        if (confirm("Bạn có chắc chắc muốn đăng ký khóa học và thanh toán ngay?")===true){
            fetch("api/registrations", {
                method: "post",
                body: JSON.stringify({
                    "name": name,
                    "phone_num": phone_num,
                    "class_id": class_id,
                    "payment_method": payment_method,
                    "payment_percent": payment_percent
                }),
                headers: {"application/json"}
            }).then(res=>res.json()).then(data=>{
                console.log(data)
            })
        }
    }
