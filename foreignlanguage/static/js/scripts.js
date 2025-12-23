    // load trang
    document.addEventListener("DOMContentLoaded", function() {
        highlightMenu();
        document.querySelectorAll('.score-input').forEach(input => {
            input.addEventListener('blur', updateDTB);
        })

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

    function getTuitionBase(course_id, level_id){
        if (!course_id || !level_id)
            return;


        document.getElementById('tuition_base').innerText = '---'
        console.log(course_id)
        console.log(level_id)

        fetch(`/api/tuition-base?course_id=${course_id}&level_id=${level_id}`,{
            method: 'GET'
        }).then(res=>res.json()).then(data=>{
            document.getElementById('tuition_base').innerText = data.tuition.toLocaleString() + ' VND'
        })
    }


