// static/js/register.js

document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('register-form');
    const passwordInput = document.getElementById('register-password');
    const togglePasswordBtn = document.getElementById('toggle-password');

    // 添加密码显示/隐藏功能
    if (togglePasswordBtn && passwordInput) {
        togglePasswordBtn.addEventListener('click', function() {
            passwordInput.type = passwordInput.type === 'password' ? 'text' : 'password';
            togglePasswordBtn.alt = passwordInput.type === 'password' ? '显示密码' : '隐藏密码';
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const username = document.getElementById('register-username').value.trim();
            const password = document.getElementById('register-password').value.trim();

            if (!username || !password) {
                alert('所有字段都不能为空。');
                return;
            }

            axios.post('/api/auth/register', {
                username: username,
                password: password,
            })
            .then(response => {
                if (response.data.code === 201) {
                    alert('注册成功，请登录。');
                    registerForm.reset();
                    window.location.href = '/login';
                } else {
                    alert(response.data.msg || '注册失败。');
                }
            })
            .catch(error => {
                console.error(error);
                alert('注册失败。');
            });
        });
    }
});
