console.log("LOADED")
function updateAvatar(obj){
    const file = obj.files[0]
    if (!file) return;

    const formData = new FormData();
    formData.append('avatar', file);

    fetch('api/student/avatar', {
        method: 'PATCH',
        body: formData
    }).then(res=>res.json()).then(data=>{
        if (data.avatar_url) {
        document.querySelectorAll('.user-avatar')
            .forEach(img => img.src = data.avatar_url);
        }
    })
}

setTimeout(function() {
    const msg = document.getElementById('status-msg');
    if (msg) {
        msg.style.opacity = '0';
        setTimeout(() => {
            msg.remove();
        }, 500);
    }
}, 3000);