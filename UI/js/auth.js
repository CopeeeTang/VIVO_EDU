/* 认证页面JavaScript - 密码显示/隐藏、表单验证等功能 */

// 认证页面相关功能
const AuthPage = {
  // 初始化认证页面
  init() {
    console.log('认证页面初始化');
    this.bindPasswordToggle();
    this.bindFormValidation();
    this.bindSocialLogin();
    this.autoFillLastUsername();
  },

  // 绑定密码显示/隐藏切换
  bindPasswordToggle() {
    const passwordToggles = document.querySelectorAll('.password-toggle');
    
    passwordToggles.forEach(toggle => {
      toggle.addEventListener('click', (e) => {
        e.preventDefault();
        const wrapper = toggle.closest('.password-wrapper');
        const input = wrapper.querySelector('.input-field');
        const toggleText = toggle.querySelector('.password-toggle-text');
        
        if (input.type === 'password') {
          input.type = 'text';
          toggleText.textContent = '隐藏';
        } else {
          input.type = 'password';
          toggleText.textContent = '显示';
        }
      });
    });
  },

  // 绑定表单验证
  bindFormValidation() {
    const forms = document.querySelectorAll('.auth-form');
    
    forms.forEach(form => {
      // 实时验证
      const inputs = form.querySelectorAll('.input-field');
      inputs.forEach(input => {
        input.addEventListener('blur', () => {
          this.validateField(input);
        });
        
        input.addEventListener('input', () => {
          this.clearFieldError(input);
        });
      });
      
      // 密码确认验证
      const password = form.querySelector('input[name="password"]');
      const confirmPassword = form.querySelector('input[name="confirmPassword"]');
      
      if (password && confirmPassword) {
        confirmPassword.addEventListener('input', () => {
          this.validatePasswordMatch(password, confirmPassword);
        });
      }
    });
  },

  // 验证单个字段
  validateField(input) {
    const value = input.value.trim();
    const fieldName = input.name;
    let isValid = true;
    let errorMessage = '';
    
    // 清除之前的错误
    this.clearFieldError(input);
    
    // 根据字段类型进行验证
    switch(fieldName) {
      case 'username':
        if (!value) {
          isValid = false;
          errorMessage = '用户名不能为空';
        } else if (value.length < 3) {
          isValid = false;
          errorMessage = '用户名长度不能少于3个字符';
        } else if (value.length > 20) {
          isValid = false;
          errorMessage = '用户名长度不能超过20个字符';
        } else if (!/^[a-zA-Z0-9_\u4e00-\u9fa5]+$/.test(value)) {
          isValid = false;
          errorMessage = '用户名只能包含字母、数字、下划线和中文';
        }
        break;
        
      case 'password':
        if (!value) {
          isValid = false;
          errorMessage = '密码不能为空';
        } else if (value.length < 6) {
          isValid = false;
          errorMessage = '密码长度不能少于6个字符';
        } else if (!/(?=.*[a-z])(?=.*[A-Z])/.test(value) && value.length < 8) {
          // 如果密码没有大小写字母组合，至少要8位
          if (!/(?=.*[0-9])/.test(value)) {
            isValid = false;
            errorMessage = '密码建议包含字母和数字';
          }
        }
        break;
        
      case 'confirmPassword':
        const passwordField = input.form.querySelector('input[name="password"]');
        if (!value) {
          isValid = false;
          errorMessage = '请确认密码';
        } else if (value !== passwordField.value) {
          isValid = false;
          errorMessage = '两次输入的密码不一致';
        }
        break;
        
      case 'email':
        if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          isValid = false;
          errorMessage = '邮箱格式不正确';
        }
        break;
        
      case 'phone':
        if (value && !/^1[3-9]\d{9}$/.test(value)) {
          isValid = false;
          errorMessage = '手机号格式不正确';
        }
        break;
    }
    
    // 显示错误消息
    if (!isValid) {
      this.showFieldError(input, errorMessage);
    }
    
    return isValid;
  },

  // 验证密码匹配
  validatePasswordMatch(password, confirmPassword) {
    if (confirmPassword.value && password.value !== confirmPassword.value) {
      this.showFieldError(confirmPassword, '两次输入的密码不一致');
      return false;
    } else {
      this.clearFieldError(confirmPassword);
      return true;
    }
  },

  // 显示字段错误
  showFieldError(input, message) {
    const inputGroup = input.closest('.input-group');
    let errorDiv = inputGroup.querySelector('.error-message');
    
    if (!errorDiv) {
      errorDiv = document.createElement('div');
      errorDiv.className = 'error-message';
      inputGroup.appendChild(errorDiv);
    }
    
    errorDiv.textContent = message;
    errorDiv.classList.add('show');
    input.classList.add('error');
  },

  // 清除字段错误
  clearFieldError(input) {
    const inputGroup = input.closest('.input-group');
    const errorDiv = inputGroup.querySelector('.error-message');
    
    if (errorDiv) {
      errorDiv.classList.remove('show');
    }
    
    input.classList.remove('error');
  },

  // 绑定社交登录
  bindSocialLogin() {
    const socialButtons = document.querySelectorAll('.social-btn');
    
    socialButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        e.preventDefault();
        const platform = button.querySelector('.btn-text').textContent;
        this.handleSocialLogin(platform);
      });
    });
  },

  // 处理社交登录
  handleSocialLogin(platform) {
    // 显示提示
    App.showModal('提示', `${platform}登录功能正在开发中`, 'info');
    
    // 这里可以集成实际的社交登录SDK
    // 例如：Google OAuth, Apple Sign In等
    console.log(`尝试使用${platform}登录`);
  },

  // 自动填充上次的用户名
  autoFillLastUsername() {
    const usernameInput = document.querySelector('input[name="username"]');
    if (usernameInput) {
      const lastUsername = localStorage.getItem('lastUsername');
      if (lastUsername) {
        usernameInput.value = lastUsername;
      }
    }
  },

  // 保存用户名到本地存储
  saveLastUsername(username) {
    if (username) {
      localStorage.setItem('lastUsername', username);
    }
  },

  // 表单提交前的完整验证
  validateForm(form) {
    const inputs = form.querySelectorAll('.input-field[required]');
    let isValid = true;
    
    inputs.forEach(input => {
      if (!this.validateField(input)) {
        isValid = false;
      }
    });
    
    // 验证复选框
    const checkboxes = form.querySelectorAll('.checkbox-input[required]');
    checkboxes.forEach(checkbox => {
      if (!checkbox.checked) {
        isValid = false;
        App.showModal('提示', '请同意用户协议和隐私政策', 'error');
      }
    });
    
    return isValid;
  },

  // 显示加载状态
  showLoadingState(button) {
    button.classList.add('loading');
    button.disabled = true;
  },

  // 隐藏加载状态
  hideLoadingState(button) {
    button.classList.remove('loading');
    button.disabled = false;
  },

  // 强密码建议
  generateStrongPassword() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    let password = '';
    
    // 确保至少包含一个大写字母、小写字母、数字和特殊字符
    password += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[Math.floor(Math.random() * 26)];
    password += 'abcdefghijklmnopqrstuvwxyz'[Math.floor(Math.random() * 26)];
    password += '0123456789'[Math.floor(Math.random() * 10)];
    password += '!@#$%^&*'[Math.floor(Math.random() * 8)];
    
    // 添加剩余的随机字符
    for (let i = 4; i < 12; i++) {
      password += chars[Math.floor(Math.random() * chars.length)];
    }
    
    // 打乱字符顺序
    return password.split('').sort(() => Math.random() - 0.5).join('');
  },

  // 密码强度检查
  checkPasswordStrength(password) {
    let strength = 0;
    let feedback = [];
    
    // 长度检查
    if (password.length >= 8) strength += 1;
    else feedback.push('至少8个字符');
    
    // 包含小写字母
    if (/[a-z]/.test(password)) strength += 1;
    else feedback.push('包含小写字母');
    
    // 包含大写字母
    if (/[A-Z]/.test(password)) strength += 1;
    else feedback.push('包含大写字母');
    
    // 包含数字
    if (/[0-9]/.test(password)) strength += 1;
    else feedback.push('包含数字');
    
    // 包含特殊字符
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength += 1;
    else feedback.push('包含特殊字符');
    
    const levels = ['很弱', '弱', '一般', '强', '很强'];
    return {
      strength: strength,
      level: levels[strength] || '很弱',
      feedback: feedback
    };
  },

  // 显示密码强度指示器
  showPasswordStrength(password, container) {
    const result = this.checkPasswordStrength(password);
    
    if (!container.querySelector('.password-strength')) {
      const strengthDiv = document.createElement('div');
      strengthDiv.className = 'password-strength';
      container.appendChild(strengthDiv);
    }
    
    const strengthDiv = container.querySelector('.password-strength');
    strengthDiv.innerHTML = `
      <div class="strength-bar">
        <div class="strength-fill strength-${result.strength}"></div>
      </div>
      <div class="strength-text">密码强度：${result.level}</div>
      ${result.feedback.length > 0 ? `<div class="strength-feedback">建议：${result.feedback.join('、')}</div>` : ''}
    `;
  }
};

// 扩展App对象的注册处理
if (typeof App !== 'undefined') {
  const originalHandleRegister = App.handleRegister;
  
  App.handleRegister = async function(formData) {
    const form = document.getElementById('registerForm');
    const submitButton = form.querySelector('button[type="submit"]');
    
    // 表单验证
    if (!AuthPage.validateForm(form)) {
      return;
    }
    
    // 显示加载状态
    AuthPage.showLoadingState(submitButton);
    
    try {
      // 保存用户名
      AuthPage.saveLastUsername(formData.get('username'));
      
      // 调用原始的注册处理函数
      await originalHandleRegister.call(this, formData);
    } catch (error) {
      console.error('注册失败:', error);
    } finally {
      // 隐藏加载状态
      AuthPage.hideLoadingState(submitButton);
    }
  };
  
  // 扩展登录处理
  const originalHandleLogin = App.handleLogin;
  
  App.handleLogin = async function(formData) {
    const form = document.querySelector('form[data-type="login"]');
    const submitButton = form?.querySelector('button[type="submit"]');
    
    if (submitButton) {
      AuthPage.showLoadingState(submitButton);
    }
    
    try {
      // 保存用户名
      AuthPage.saveLastUsername(formData.get('username'));
      
      // 调用原始的登录处理函数
      await originalHandleLogin.call(this, formData);
    } catch (error) {
      console.error('登录失败:', error);
    } finally {
      if (submitButton) {
        AuthPage.hideLoadingState(submitButton);
      }
    }
  };
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
  // 只在认证页面初始化
  if (document.querySelector('.auth-page')) {
    AuthPage.init();
  }
});

// 密码强度样式（通过JavaScript动态添加）
const passwordStrengthStyles = `
  .password-strength {
    margin-top: 8px;
    font-size: 0.8rem;
  }
  
  .strength-bar {
    width: 100%;
    height: 4px;
    background: #e0e0e0;
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 4px;
  }
  
  .strength-fill {
    height: 100%;
    transition: width 0.3s ease;
  }
  
  .strength-fill.strength-1 { width: 20%; background: #ff4444; }
  .strength-fill.strength-2 { width: 40%; background: #ff8800; }
  .strength-fill.strength-3 { width: 60%; background: #ffcc00; }
  .strength-fill.strength-4 { width: 80%; background: #88cc00; }
  .strength-fill.strength-5 { width: 100%; background: #44aa00; }
  
  .strength-text {
    color: #666;
    font-weight: 500;
  }
  
  .strength-feedback {
    color: #888;
    font-size: 0.75rem;
    margin-top: 2px;
  }
`;

// 动态添加密码强度样式
if (!document.getElementById('password-strength-styles')) {
  const style = document.createElement('style');
  style.id = 'password-strength-styles';
  style.textContent = passwordStrengthStyles;
  document.head.appendChild(style);
}

// 导出到全局作用域
window.AuthPage = AuthPage; 