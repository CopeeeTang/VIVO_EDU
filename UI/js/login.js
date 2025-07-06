/**
 * 登录页面JavaScript功能
 * 处理登录表单提交、密码显示/隐藏、社交登录、登录成功弹窗等功能
 */

(function() {
    'use strict';
    
    // 登录页面功能模块
    class LoginManager {
        constructor() {
            this.isLoading = false;
            this.init();
        }
        
        init() {
            this.bindEvents();
            this.updateTime();
            // 每秒更新时间
            setInterval(() => this.updateTime(), 1000);
        }
        
        bindEvents() {
            // 密码切换显示/隐藏
            const passwordToggle = document.getElementById('passwordToggle');
            const passwordInput = document.getElementById('password');
            
            if (passwordToggle && passwordInput) {
                passwordToggle.addEventListener('click', () => {
                    this.togglePassword(passwordInput, passwordToggle);
                });
            }
            
            // 表单提交
            const loginButton = document.getElementById('loginButton');
            const usernameInput = document.getElementById('username');
            
            if (loginButton) {
                loginButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.handleLogin();
                });
            }
            
            // 回车键提交
            document.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !this.isLoading) {
                    this.handleLogin();
                }
            });
            
            // 输入框焦点事件
            [usernameInput, passwordInput].forEach(input => {
                if (input) {
                    input.addEventListener('focus', () => this.clearError(input));
                    input.addEventListener('blur', () => this.validateField(input));
                }
            });
            
            // 社交登录
            const googleButton = document.querySelector('.google-login');
            const appleButton = document.querySelector('.apple-login');
            
            if (googleButton) {
                googleButton.addEventListener('click', () => this.handleSocialLogin('google'));
            }
            
            if (appleButton) {
                appleButton.addEventListener('click', () => this.handleSocialLogin('apple'));
            }
            
            // 弹窗关闭
            const closeModal = document.getElementById('closeModal');
            const successModal = document.getElementById('successModal');
            
            if (closeModal) {
                closeModal.addEventListener('click', () => this.closeSuccessModal());
            }
            
            if (successModal) {
                successModal.addEventListener('click', (e) => {
                    if (e.target === successModal) {
                        this.closeSuccessModal();
                    }
                });
            }
        }
        
        updateTime() {
            const timeElement = document.querySelector('.time');
            if (timeElement) {
                const now = new Date();
                const hours = now.getHours().toString().padStart(2, '0');
                const minutes = now.getMinutes().toString().padStart(2, '0');
                timeElement.textContent = `${hours}:${minutes}`;
            }
        }
        
        togglePassword(input, toggle) {
            if (input.type === 'password') {
                input.type = 'text';
                toggle.classList.add('active');
            } else {
                input.type = 'password';
                toggle.classList.remove('active');
            }
        }
        
        validateField(input) {
            const wrapper = input.closest('.input-wrapper');
            const field = input.closest('.input-field');
            
            if (!input.value.trim()) {
                this.showFieldError(wrapper, field, '此字段不能为空');
                return false;
            }
            
            if (input.id === 'username') {
                if (input.value.length < 3) {
                    this.showFieldError(wrapper, field, '账号至少需要3个字符');
                    return false;
                }
            }
            
            if (input.id === 'password') {
                if (input.value.length < 6) {
                    this.showFieldError(wrapper, field, '密码至少需要6个字符');
                    return false;
                }
            }
            
            this.showFieldSuccess(wrapper, field);
            return true;
        }
        
        showFieldError(wrapper, field, message) {
            wrapper.classList.remove('success');
            wrapper.classList.add('error');
            field.classList.add('error');
            
            // 移除之前的错误消息
            const existingError = field.querySelector('.error-message');
            if (existingError) {
                existingError.remove();
            }
            
            // 添加错误消息
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = message;
            errorDiv.style.cssText = `
                color: var(--required-color);
                font-size: 12px;
                margin-top: 5px;
                padding-left: 15px;
            `;
            field.appendChild(errorDiv);
        }
        
        showFieldSuccess(wrapper, field) {
            wrapper.classList.remove('error');
            wrapper.classList.add('success');
            field.classList.remove('error');
            
            // 移除错误消息
            const errorMessage = field.querySelector('.error-message');
            if (errorMessage) {
                errorMessage.remove();
            }
        }
        
        clearError(input) {
            const wrapper = input.closest('.input-wrapper');
            const field = input.closest('.input-field');
            
            wrapper.classList.remove('error');
            field.classList.remove('error');
            
            const errorMessage = field.querySelector('.error-message');
            if (errorMessage) {
                errorMessage.remove();
            }
        }
        
        async handleLogin() {
            if (this.isLoading) return;
            
            const usernameInput = document.getElementById('username');
            const passwordInput = document.getElementById('password');
            const loginButton = document.getElementById('loginButton');
            
            // 验证输入
            const isUsernameValid = this.validateField(usernameInput);
            const isPasswordValid = this.validateField(passwordInput);
            
            if (!isUsernameValid || !isPasswordValid) {
                return;
            }
            
            // 开始加载
            this.isLoading = true;
            loginButton.classList.add('loading');
            loginButton.disabled = true;
            
            try {
                // 模拟API调用
                const loginData = {
                    username: usernameInput.value.trim(),
                    password: passwordInput.value
                };
                
                // 这里应该调用实际的登录API
                const response = await this.callLoginAPI(loginData);
                
                if (response.success) {
                    // 存储用户信息
                    localStorage.setItem('userToken', response.token);
                    localStorage.setItem('userInfo', JSON.stringify(response.user));
                    
                    // 显示成功弹窗
                    this.showSuccessModal();
                    
                    // 3秒后跳转到主页
                    setTimeout(() => {
                        window.location.href = 'home.html';
                    }, 3000);
                } else {
                    this.showLoginError(response.message || '登录失败，请检查账号密码');
                }
            } catch (error) {
                console.error('登录错误:', error);
                this.showLoginError('网络错误，请稍后重试');
            } finally {
                this.isLoading = false;
                loginButton.classList.remove('loading');
                loginButton.disabled = false;
            }
        }
        
        async callLoginAPI(loginData) {
            // 模拟API延迟
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // 模拟登录逻辑（实际项目中替换为真实API调用）
            if (loginData.username === 'admin' && loginData.password === '123456') {
                return {
                    success: true,
                    token: 'mock-jwt-token-' + Date.now(),
                    user: {
                        id: 1,
                        username: loginData.username,
                        name: '测试用户',
                        avatar: null
                    }
                };
            } else {
                return {
                    success: false,
                    message: '账号或密码错误'
                };
            }
        }
        
        showLoginError(message) {
            // 显示错误提示
            const errorDiv = document.createElement('div');
            errorDiv.className = 'login-error';
            errorDiv.textContent = message;
            errorDiv.style.cssText = `
                background: rgba(248, 97, 76, 0.1);
                color: var(--required-color);
                padding: 12px 15px;
                border-radius: 8px;
                margin: 10px 0;
                font-size: 14px;
                text-align: center;
                border: 1px solid rgba(248, 97, 76, 0.3);
            `;
            
            const formWrapper = document.querySelector('.form-wrapper');
            const existingError = formWrapper.querySelector('.login-error');
            
            if (existingError) {
                existingError.remove();
            }
            
            formWrapper.insertBefore(errorDiv, formWrapper.firstChild);
            
            // 3秒后自动移除错误提示
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.remove();
                }
            }, 3000);
        }
        
        showSuccessModal() {
            const modal = document.getElementById('successModal');
            if (modal) {
                modal.classList.add('show');
            }
        }
        
        closeSuccessModal() {
            const modal = document.getElementById('successModal');
            if (modal) {
                modal.classList.remove('show');
            }
        }
        
        handleSocialLogin(provider) {
            console.log(`${provider} 登录功能开发中...`);
            
            // 显示提示
            const message = provider === 'google' ? 'Google 登录功能开发中...' : 'Apple 登录功能开发中...';
            
            const toast = document.createElement('div');
            toast.textContent = message;
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: var(--primary-color);
                color: white;
                padding: 12px 24px;
                border-radius: 25px;
                z-index: 3000;
                font-size: 14px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            `;
            
            document.body.appendChild(toast);
            
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 2000);
        }
    }
    
    // 页面加载完成后初始化
    document.addEventListener('DOMContentLoaded', () => {
        new LoginManager();
    });
    
    // 全局错误处理
    window.addEventListener('error', (event) => {
        console.error('页面错误:', event.error);
    });
    
    // 页面可见性变化时更新时间
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            const timeElement = document.querySelector('.time');
            if (timeElement) {
                const now = new Date();
                const hours = now.getHours().toString().padStart(2, '0');
                const minutes = now.getMinutes().toString().padStart(2, '0');
                timeElement.textContent = `${hours}:${minutes}`;
            }
        }
    });
})(); 