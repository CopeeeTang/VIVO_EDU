/* 主要JavaScript文件 - 页面导航、模态框、表单处理、数据获取等功能 */

// 应用程序主对象
const App = {
  // 初始化应用程序
  init() {
    console.log('应用程序初始化');
    this.bindEvents();
    this.loadStoredData();
  },

  // 绑定事件监听器
  bindEvents() {
    // 模态框关闭事件
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal')) {
        this.closeModal();
      }
    });

    // 表单提交事件
    document.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleFormSubmit(e);
    });

    // 导航点击事件
    document.addEventListener('click', (e) => {
      if (e.target.closest('[data-navigate]')) {
        const target = e.target.closest('[data-navigate]');
        const page = target.dataset.navigate;
        this.navigateTo(page);
      }
    });
  },

  // 页面导航功能
  navigateTo(pageName) {
    const currentPage = window.location.pathname.split('/').pop().replace('.html', '');
    
    // 防止重复导航
    if (currentPage === pageName) return;
    
    // 特殊导航逻辑
    switch(pageName) {
      case 'login':
        if (this.isUserLoggedIn()) {
          this.navigateTo('home');
          return;
        }
        break;
      case 'home':
        if (!this.isUserLoggedIn()) {
          this.navigateTo('login');
          return;
        }
        break;
    }
    
    // 执行导航
    window.location.href = `${pageName}.html`;
  },

  // 返回上一页功能
  goBack() {
    const currentPage = window.location.pathname.split('/').pop().replace('.html', '');
    
    // 根据当前页面决定返回逻辑
    switch(currentPage) {
      case 'education-overview':
      case 'conflict-analysis':
        // 从子页面返回报告页面
        this.navigateTo('report');
        break;
      case 'report':
        // 从报告页面返回历史记录页面
        this.navigateTo('history');
        break;
      case 'history':
        // 从历史记录页面返回主页
        this.navigateTo('home');
        break;
      default:
        // 默认使用浏览器历史记录
        if (window.history.length > 1) {
          window.history.back();
        } else {
          // 如果没有历史记录，返回主页
          this.navigateTo('home');
        }
        break;
    }
  },

  // 模态框控制
  showModal(title, message, type = 'info') {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-title">${title}</div>
        <div class="modal-text">${message}</div>
        <button class="btn btn-primary" onclick="App.closeModal()">确定</button>
      </div>
    `;
    document.body.appendChild(modal);
    
    // 自动关闭（成功消息）
    if (type === 'success') {
      setTimeout(() => {
        this.closeModal();
      }, 2000);
    }
  },

  closeModal() {
    const modal = document.querySelector('.modal.active');
    if (modal) {
      modal.remove();
    }
  },

  // 表单处理
  handleFormSubmit(e) {
    const form = e.target;
    const formData = new FormData(form);
    const formType = form.dataset.type;
    
    switch(formType) {
      case 'register':
        this.handleRegister(formData);
        break;
      case 'login':
        this.handleLogin(formData);
        break;
      case 'upload':
        this.handleUpload(formData);
        break;
      default:
        console.log('未知表单类型:', formType);
    }
  },

  // 注册处理
  async handleRegister(formData) {
    const username = formData.get('username');
    const password = formData.get('password');
    const confirmPassword = formData.get('confirmPassword');
    
    // 表单验证
    if (!username || !password || !confirmPassword) {
      this.showModal('错误', '请填写完整信息', 'error');
      return;
    }
    
    if (password !== confirmPassword) {
      this.showModal('错误', '两次密码输入不一致', 'error');
      return;
    }
    
    try {
      // 模拟API调用
      const response = await this.apiCall('/api/register', {
        username,
        password
      });
      
      if (response.success) {
        this.showModal('成功', '注册成功！正在跳转到登录页面...', 'success');
        setTimeout(() => {
          this.navigateTo('login');
        }, 2000);
      } else {
        this.showModal('错误', response.message || '注册失败', 'error');
      }
    } catch (error) {
      this.showModal('错误', '网络错误，请稍后重试', 'error');
    }
  },

  // 登录处理
  async handleLogin(formData) {
    const username = formData.get('username');
    const password = formData.get('password');
    
    if (!username || !password) {
      this.showModal('错误', '请输入用户名和密码', 'error');
      return;
    }
    
    try {
      // 模拟API调用
      const response = await this.apiCall('/api/login', {
        username,
        password
      });
      
      if (response.success) {
        // 存储用户信息
        this.setUserToken(response.token);
        this.setUserInfo(response.user);
        
        this.showModal('成功', '登录成功！正在跳转...', 'success');
        setTimeout(() => {
          this.navigateTo('home');
        }, 2000);
      } else {
        this.showModal('错误', response.message || '登录失败', 'error');
      }
    } catch (error) {
      this.showModal('错误', '网络错误，请稍后重试', 'error');
    }
  },

  // 文件上传处理
  async handleUpload(formData) {
    const file = formData.get('audioFile');
    const childName = formData.get('childName');
    const recordDate = formData.get('recordDate');
    
    if (!file) {
      this.showModal('错误', '请选择要上传的文件', 'error');
      return;
    }
    
    if (!childName || !recordDate) {
      this.showModal('错误', '请填写儿童姓名和录制日期', 'error');
      return;
    }
    
    try {
      // 显示上传进度
      this.showUploadProgress();
      
      // 模拟API调用
      const response = await this.apiCall('/api/upload', formData, true);
      
      if (response.success) {
        this.hideUploadProgress();
        this.showModal('成功', '文件上传成功！正在处理...', 'success');
        setTimeout(() => {
          this.navigateTo('history');
        }, 2000);
      } else {
        this.hideUploadProgress();
        this.showModal('错误', response.message || '上传失败', 'error');
      }
    } catch (error) {
      this.hideUploadProgress();
      this.showModal('错误', '上传失败，请稍后重试', 'error');
    }
  },

  // 显示上传进度
  showUploadProgress() {
    const progress = document.createElement('div');
    progress.id = 'upload-progress';
    progress.className = 'modal active';
    progress.innerHTML = `
      <div class="modal-content">
        <div class="modal-title">上传中...</div>
        <div class="progress-bar">
          <div class="progress-fill"></div>
        </div>
        <div class="modal-text">请稍候，正在上传文件</div>
      </div>
    `;
    document.body.appendChild(progress);
    
    // 模拟进度条
    let progress_value = 0;
    const progressFill = progress.querySelector('.progress-fill');
    const interval = setInterval(() => {
      progress_value += Math.random() * 10;
      if (progress_value >= 100) {
        progress_value = 100;
        clearInterval(interval);
      }
      progressFill.style.width = progress_value + '%';
    }, 200);
  },

  hideUploadProgress() {
    const progress = document.getElementById('upload-progress');
    if (progress) {
      progress.remove();
    }
  },

  // 录音功能
  recording: {
    isRecording: false,
    mediaRecorder: null,
    audioChunks: [],
    
    async startRecording() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.mediaRecorder = new MediaRecorder(stream);
        this.audioChunks = [];
        
        this.mediaRecorder.addEventListener('dataavailable', (event) => {
          this.audioChunks.push(event.data);
        });
        
        this.mediaRecorder.addEventListener('stop', () => {
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
          this.handleRecordingComplete(audioBlob);
        });
        
        this.mediaRecorder.start();
        this.isRecording = true;
        
        // 更新UI
        document.querySelectorAll('.recording-indicator').forEach(el => {
          el.classList.add('active');
        });
        
        App.showModal('提示', '录音已开始', 'info');
      } catch (error) {
        App.showModal('错误', '无法访问麦克风，请检查权限设置', 'error');
      }
    },
    
    stopRecording() {
      if (this.mediaRecorder && this.isRecording) {
        this.mediaRecorder.stop();
        this.isRecording = false;
        
        // 停止所有音频轨道
        this.mediaRecorder.stream.getTracks().forEach(track => {
          track.stop();
        });
        
        // 更新UI
        document.querySelectorAll('.recording-indicator').forEach(el => {
          el.classList.remove('active');
        });
      }
    },
    
    handleRecordingComplete(audioBlob) {
      // 存储录音数据
      const recordingData = {
        blob: audioBlob,
        timestamp: Date.now(),
        duration: this.getRecordingDuration()
      };
      
      // 显示录音完成选项
      this.showRecordingOptions(recordingData);
    },
    
    showRecordingOptions(recordingData) {
      const modal = document.createElement('div');
      modal.className = 'modal active';
      modal.innerHTML = `
        <div class="modal-content">
          <div class="modal-title">录音完成</div>
          <div class="modal-text">录音时长：${this.formatDuration(recordingData.duration)}</div>
          <div class="flex gap-medium">
            <button class="btn btn-outline" onclick="App.recording.discardRecording()">取消</button>
            <button class="btn btn-primary" onclick="App.recording.saveRecording()">保存</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
      
      // 存储临时录音数据
      this.tempRecording = recordingData;
    },
    
    discardRecording() {
      this.tempRecording = null;
      App.closeModal();
    },
    
    saveRecording() {
      if (this.tempRecording) {
        // 显示保存表单
        this.showSaveForm(this.tempRecording);
      }
    },
    
    showSaveForm(recordingData) {
      App.closeModal();
      
      const modal = document.createElement('div');
      modal.className = 'modal active';
      modal.innerHTML = `
        <div class="modal-content">
          <div class="modal-title">保存录音</div>
          <form data-type="save-recording">
            <div class="input-group">
              <label class="input-label">儿童姓名</label>
              <input type="text" class="input-field" name="childName" required>
            </div>
            <div class="input-group">
              <label class="input-label">录制日期</label>
              <input type="date" class="input-field" name="recordDate" required>
            </div>
            <div class="flex gap-medium">
              <button type="button" class="btn btn-outline" onclick="App.closeModal()">取消</button>
              <button type="submit" class="btn btn-primary">保存</button>
            </div>
          </form>
        </div>
      `;
      document.body.appendChild(modal);
    },
    
    formatDuration(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    },
    
    getRecordingDuration() {
      // 这里应该实际计算录音时长
      return Math.floor(Math.random() * 300) + 30; // 模拟30-330秒的录音
    }
  },

  // 数据管理
  setUserToken(token) {
    localStorage.setItem('userToken', token);
  },

  getUserToken() {
    return localStorage.getItem('userToken');
  },

  setUserInfo(user) {
    localStorage.setItem('userInfo', JSON.stringify(user));
  },

  getUserInfo() {
    const userStr = localStorage.getItem('userInfo');
    return userStr ? JSON.parse(userStr) : null;
  },

  isUserLoggedIn() {
    return !!this.getUserToken();
  },

  logout() {
    localStorage.removeItem('userToken');
    localStorage.removeItem('userInfo');
    this.navigateTo('login');
  },

  // 加载存储的数据
  loadStoredData() {
    const userInfo = this.getUserInfo();
    if (userInfo) {
      // 更新页面中的用户信息
      this.updateUserInfo(userInfo);
    }
  },

  updateUserInfo(userInfo) {
    const userElements = document.querySelectorAll('[data-user-info]');
    userElements.forEach(el => {
      const field = el.dataset.userInfo;
      if (userInfo[field]) {
        el.textContent = userInfo[field];
      }
    });
  },

  // API调用函数
  async apiCall(endpoint, data, isFormData = false) {
    const token = this.getUserToken();
    const headers = {
      'Authorization': token ? `Bearer ${token}` : ''
    };
    
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: isFormData ? data : JSON.stringify(data)
      });
      
      return await response.json();
    } catch (error) {
      throw new Error('网络请求失败');
    }
  },

  // 获取历史报告
  async getHistoryReports() {
    try {
      const response = await this.apiCall('/api/reports', {}, false);
      return response.data || [];
    } catch (error) {
      console.error('获取历史报告失败:', error);
      return [];
    }
  },

  // 获取报告详情
  async getReportDetail(reportId) {
    try {
      const response = await this.apiCall(`/api/reports/${reportId}`, {}, false);
      return response.data || {};
    } catch (error) {
      console.error('获取报告详情失败:', error);
      return {};
    }
  },

  // 删除报告
  async deleteReport(reportId) {
    try {
      const response = await this.apiCall(`/api/reports/${reportId}/delete`, {}, false);
      return response.success;
    } catch (error) {
      console.error('删除报告失败:', error);
      return false;
    }
  },

  // 工具函数
  utils: {
    // 格式化日期
    formatDate(date) {
      return new Date(date).toLocaleDateString('zh-CN');
    },
    
    // 格式化时间
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    },
    
    // 生成随机ID
    generateId() {
      return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },
    
    // 防抖函数
    debounce(func, wait) {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    }
  }
};

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});

// 全局错误处理
window.addEventListener('error', (e) => {
  console.error('全局错误:', e.error);
  // 可以在这里添加错误上报逻辑
});

// 导出到全局作用域
window.App = App; 