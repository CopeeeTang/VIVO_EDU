// static/js/login.js

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const passwordInput = document.getElementById('login-password');
    const togglePasswordBtn = document.getElementById('toggle-password');

    // 简化密码显示/隐藏功能
    if (togglePasswordBtn && passwordInput) {
        togglePasswordBtn.addEventListener('click', function() {
            // 只切换密码输入框的类型
            passwordInput.type = passwordInput.type === 'password' ? 'text' : 'password';
            // 更新图标的alt文本
            togglePasswordBtn.alt = passwordInput.type === 'password' ? '显示密码' : '隐藏密码';
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const username = document.getElementById('login-username').value.trim();
            const password = document.getElementById('login-password').value.trim();

            if (!username || !password) {
                alert('用户名和密码不能为空。');
                return;
            }

            axios.post('/api/auth/login', {
                username: username,
                password: password
            }, {
                // 不需要设置 withCredentials，除非您同时使用 Cookie
            })
            .then(response => {
                if (response.data.code === 200) {
                    alert('登录成功。');
                    loginForm.reset();
                    // 存储 JWT 令牌
                    localStorage.setItem('jwtToken', response.data.data.access_token); // 保持 'jwtToken'
                    // 设置 Axios 默认头部
                    axios.defaults.headers.common['Authorization'] = 'Bearer ' + response.data.data.access_token;
                    // 跳转到上传页面
                    window.location.href = '/home_page';
                } else {
                    alert(response.data.msg || '登录失败。');
                }
            })
            .catch(error => {
                console.error(error);
                if (error.response && error.response.data.msg === '用户名或密码错误') {
                    alert('登录失败：用户名或密码错误。');
                } else {
                    alert('登录失败。');
                }
            });
        });
    }

    // 添加登出功能（可选）
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            axios.post('/api/auth/logout', {}, {
                // 不需要附带 Authorization 头，因为后台基于 Cookie 验证（如果有）
            })
            .then(response => {
                if (response.data.msg === '登出成功') {
                    alert('已登出。');
                    // 清除存储的 JWT 令牌
                    localStorage.removeItem('jwtToken');
                    // 清除 Axios 默认头部
                    delete axios.defaults.headers.common['Authorization'];
                    window.location.href = '/login';
                }
            })
            .catch(error => {
                console.error(error);
                alert('登出失败。');
            });
        });
    }
});
