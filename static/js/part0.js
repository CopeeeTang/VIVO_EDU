// 从 URL 获取 file_id
function getFileIdFromUrl() {
    // 首先尝试从URL查询参数中获取
    const urlParams = new URLSearchParams(window.location.search);
    const fileIdFromParams = urlParams.get('file_id');
    if (fileIdFromParams) {
        return fileIdFromParams;
    }
    
    // 如果查询参数中没有，尝试从URL路径中提取
    // 例如从 /static/reports/output0_4097534a-59c6-4c0d-bb37-cedd7cc54a60.html 提取
    const pathMatch = window.location.pathname.match(/output\d+_([0-9a-fA-F-]+)\.html/);
    if (pathMatch && pathMatch[1]) {
        return pathMatch[1];
    }
    
    // 如果仍然没有，返回null
    return null;
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面DOM加载完成');
    
    const fileId = getFileIdFromUrl();
    console.log('获取到的文件ID:', fileId);
    
    // 即使没有file_id也继续执行，只是记录警告
    if (!fileId) {
        console.warn('警告: 未找到 file_id，部分功能可能无法正常使用');
    }

    // 检查登录状态
    const token = localStorage.getItem('jwtToken');
    console.log('JWT令牌存在:', !!token);
                 
    if (!token) {
        console.warn('警告: 未找到认证令牌，评分功能可能无法使用');
        const loginMessage = document.getElementById('login-status-message');
        if (loginMessage) {
            loginMessage.style.display = 'block';
        }
    }

    // 只有在有fileId的情况下更新链接
    if (fileId) {
        // 更新所有跳转链接的 file_id
        const links = document.querySelectorAll('a[href*="output"]');
        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href.includes('output') && href.includes('{{ file_id }}')) {
                // 替换链接中的 file_id 占位符
                link.href = href.replace('{{ file_id }}', fileId);
            }
        });
    }
    
    // 添加CSS样式到头部
    const style = document.createElement('style');
    style.textContent = `
        .rating-stars i.active {
            color: #ffcc00 !important;
        }
        .rating-stars i:hover {
            color: #ffaa00;
            cursor: pointer;
        }
        .thank-you-message {
            display: none;
            color: #27ae60;
            margin-top: 20px;
            background-color: #f0fff4;
            border: 1px solid #a3e4b8;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        .thank-you-icon {
            font-size: 24px;
            color: #27ae60;
            margin-bottom: 10px;
        }
        .thank-you-text {
            font-size: 18px;
            font-weight: bold;
        }
    `;
    document.head.appendChild(style);
    
    // 确保表单正确初始化
    console.log('正在初始化评分系统...');
    initRatingSystem();

    // 添加表单提交事件处理
    const ratingForms = document.querySelectorAll('form[id^="rating-form-"]');
    console.log('找到评分表单数量:', ratingForms.length);
    
    ratingForms.forEach((form, index) => {
        console.log(`表单${index+1}:`, form.id);
        
        // 确保表单不会通过常规方式提交
        form.setAttribute('method', 'post');
        form.setAttribute('action', 'javascript:void(0);');
        form.setAttribute('onsubmit', 'return false;');
        
        // 移除已有的事件监听器(如果有)
        form.removeEventListener('submit', handleRatingSubmit);
        
        // 添加新的事件监听器
        form.addEventListener('submit', handleRatingSubmit);
        
        // 检查提交按钮
        const submitButton = form.querySelector('.rating-submit');
        if (submitButton) {
            console.log(`找到表单${index+1}的提交按钮`);
            
            // 添加额外的点击事件用于调试
            submitButton.addEventListener('click', function(e) {
                console.log(`表单${index+1}的提交按钮被点击`, e);
                // 测试提交按钮是否在form内部
                console.log('按钮所在表单:', this.closest('form') ? this.closest('form').id : '无法找到表单');
                
                // 确保点击按钮时表单提交事件被触发
                setTimeout(() => {
                    if (form && typeof form.dispatchEvent === 'function') {
                        console.log('手动触发表单提交事件');
                        try {
                            const submitEvent = new Event('submit', {
                                bubbles: true,
                                cancelable: true
                            });
                            form.dispatchEvent(submitEvent);
                        } catch (error) {
                            console.error('触发表单提交事件失败:', error);
                            // 直接调用处理函数
                            handleRatingSubmit({
                                preventDefault: () => {},
                                target: form
                            });
                        }
                    }
                }, 100);
            });
        } else {
            console.error(`未找到表单${index+1}的提交按钮`);
        }
    });
    
    // 将提交函数暴露为全局函数，方便在控制台调用
    window.testSubmitRating = function(formId) {
        const form = document.getElementById(formId || 'rating-form-part0');
        if (!form) {
            console.error('未找到指定的表单');
            return;
        }
        
        // 填充所有必填字段
        form.querySelectorAll('.rating-input').forEach(input => {
            if (!input.value) {
                input.value = 5; // 默认填充5分
            }
        });
        
        console.log('手动触发表单提交');
        form.dispatchEvent(new Event('submit'));
    };
    
    console.log('初始化完成。可以在控制台使用testSubmitRating()函数测试提交');

    // Setup collapsible sections
    setupCollapsibleSections();
});

// 处理评分表单提交
function handleRatingSubmit(event) {
    event.preventDefault();
    console.log('表单提交处理函数被触发');
    
    // 获取表单数据
    const formData = new FormData(event.target);
    console.log('表单数据:', [...formData.entries()]);
    
    // 获取令牌
    const token = localStorage.getItem('jwtToken');
    console.log('JWT令牌存在:', !!token);
    
    // 即使没有token也尝试提交
    if (!token) {
        console.warn('警告: 未找到认证令牌，将尝试无令牌提交');
    }
    
    // 使用fetch API提交表单，并附加Authorization头
    console.log('准备发送API请求...');
    
    // 使用绝对路径
    const apiUrl = window.location.origin + '/api/audio/submit_rating';
    console.log('API请求地址:', apiUrl);
    
    // 准备headers
    const headers = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    fetch(apiUrl, {
        method: 'POST',
        headers: headers,
        body: formData
    })
    .then(response => {
        console.log('收到API响应:', response.status, response.statusText);
        if (!response.ok) {
            throw new Error(`HTTP错误! 状态: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('评分提交成功:', data);
        
        // 显示成功提示弹窗
        alert('评分提交成功！感谢您的反馈');
        
        // 隐藏整个表单，只显示感谢信息
        const ratingCriteria = event.target.closest('.rating-criteria');
        console.log('评分区域元素:', !!ratingCriteria);
        
        if (ratingCriteria) {
            const form = ratingCriteria.querySelector('form');
            console.log('表单元素:', !!form);
            
            if (form) {
                form.style.display = 'none';
            }
            
            // 显示感谢信息
            const thankYouMessage = ratingCriteria.querySelector('.thank-you-message');
            console.log('感谢信息元素:', !!thankYouMessage);
            
            if (thankYouMessage) {
                thankYouMessage.style.display = 'block';
            }
        }
    })
    .catch(error => {
        console.error('评分提交失败:', error);
        alert('评分提交失败，请稍后再试: ' + error.message);
    });
}

// 评分系统初始化 - 使用数字输入框
function initRatingSystem() {
    console.log('初始化评分系统...');
    
    // 获取所有评分输入框
    const ratingInputs = document.querySelectorAll('.rating-input');
    
    // 为每个输入框添加验证逻辑
    ratingInputs.forEach(input => {
        input.addEventListener('input', function() {
            // 获取输入值
            let value = parseInt(this.value);
            
            // 验证范围
            if (isNaN(value) || value < 1 || value > 5) {
                // 不满足条件时添加错误样式
                this.classList.add('input-error');
            } else {
                // 满足条件时移除错误样式
                this.classList.remove('input-error');
                
                // 根据评分数值调整输入框颜色
                updateInputColor(this, value);
            }
        });
        
        // 失去焦点时验证
        input.addEventListener('blur', function() {
            let value = parseInt(this.value);
            
            // 如果不是有效数字或超出范围，设为空
            if (isNaN(value) || value < 1 || value > 5) {
                this.value = '';
                this.classList.remove('input-error');
            }
        });
    });
    
    // 表单提交处理
    const forms = document.querySelectorAll('form[id^="rating-form-"]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('initRatingSystem中的表单提交被触发');
            
            // 检查是否所有评分都已填写
            const inputs = Array.from(this.querySelectorAll('.rating-input'));
            const emptyInputs = inputs.filter(input => !input.value);
            
            if (emptyInputs.length > 0) {
                // 标记未填写的输入框
                emptyInputs.forEach(input => {
                    input.classList.add('input-error');
                });
                
                alert('请为所有项目评分（1-5分）');
                return;
            }
            
            // 获取表单数据
            const formData = new FormData(this);
            console.log('表单数据:', [...formData.entries()]);
            
            // 获取令牌
            const token = localStorage.getItem('jwtToken');
            console.log('JWT令牌存在:', !!token);
            
            // 即使没有token也尝试提交
            if (!token) {
                console.warn('警告: 未找到认证令牌，将尝试无令牌提交');
            }
            
            // 使用fetch API提交表单
            console.log('准备发送API请求...');
            
            // 使用绝对路径
            const apiUrl = window.location.origin + '/api/audio/submit_rating';
            console.log('API请求地址:', apiUrl);
            
            // 准备headers
            const headers = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            fetch(apiUrl, {
                method: 'POST',
                headers: headers,
                body: formData
            })
            .then(response => {
                console.log('收到API响应:', response.status, response.statusText);
                if (!response.ok) {
                    throw new Error(`HTTP错误! 状态: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('评分提交成功:', data);
                
                // 显示成功提示弹窗
                alert('评分提交成功！感谢您的反馈');
                
                // 隐藏整个表单，只显示感谢信息
                const ratingCriteria = this.closest('.rating-criteria');
                console.log('评分区域元素:', !!ratingCriteria);
                
                if (ratingCriteria) {
                    const form = ratingCriteria.querySelector('form');
                    console.log('表单元素:', !!form);
                    
                    if (form) {
                        form.style.display = 'none';
                    }
                    
                    // 显示感谢信息
                    const thankYouMessage = ratingCriteria.querySelector('.thank-you-message');
                    console.log('感谢信息元素:', !!thankYouMessage);
                    
                    if (thankYouMessage) {
                        thankYouMessage.style.display = 'block';
                    }
                }
            })
            .catch(error => {
                console.error('评分提交失败:', error);
                alert('评分提交失败，请稍后再试: ' + error.message);
            });
        });
    });
}

// 根据评分更新输入框颜色
function updateInputColor(input, value) {
    // 移除所有可能的颜色类
    input.classList.remove('rating-low', 'rating-medium', 'rating-high');
    
    // 根据评分添加对应的颜色类
    if (value <= 2) {
        input.classList.add('rating-low');
    } else if (value <= 3) {
        input.classList.add('rating-medium');
    } else {
        input.classList.add('rating-high');
    }
}

// 添加评分颜色样式
function addRatingStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .rating-input.input-error {
            border-color: #ff6b6b !important;
            background-color: #fff0f0 !important;
        }
        
        .rating-input.rating-low {
            border-color: #ff9f67;
            color: #e67e22;
        }
        
        .rating-input.rating-medium {
            border-color: #ffdb58;
            color: #f39c12;
        }
        
        .rating-input.rating-high {
            border-color: #7fd8a6;
            color: #27ae60;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .thank-you-message {
            animation: fadeIn 0.5s ease;
        }
    `;
    document.head.appendChild(style);
}

function setupCollapsibleSections() {
    const headers = document.querySelectorAll('.collapsible-header');

    headers.forEach(header => {
        header.addEventListener('click', function() {
            const section = this.closest('.collapsible-section');
            if (section) {
                section.classList.toggle('expanded');
                section.classList.toggle('collapsed'); // Toggle both for potential initial state setting
            }
        });
    });
}
