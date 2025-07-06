/**
 * 错误页面JavaScript功能
 * 处理错误弹窗的关闭、确认等交互功能
 */

(function() {
    'use strict';
    
    // 错误页面类
    class ErrorPage {
        constructor() {
            this.errorModal = document.getElementById('errorModal');
            this.errorClose = document.getElementById('errorClose');
            this.errorConfirm = document.getElementById('errorConfirm');
            this.errorOverlay = document.querySelector('.error-overlay');
            
            // 绑定事件
            this.bindEvents();
            
            // 初始化
            this.init();
        }
        
        /**
         * 初始化
         */
        init() {
            // 设置焦点到确认按钮
            this.setInitialFocus();
            
            // 显示错误弹窗动画
            this.showErrorModal();
            
            // 记录错误信息
            this.logErrorInfo();
        }
        
        /**
         * 绑定事件
         */
        bindEvents() {
            // 关闭按钮点击
            if (this.errorClose) {
                this.errorClose.addEventListener('click', () => this.closeErrorModal());
            }
            
            // 确认按钮点击
            if (this.errorConfirm) {
                this.errorConfirm.addEventListener('click', () => this.confirmError());
            }
            
            // 遮罩层点击
            if (this.errorOverlay) {
                this.errorOverlay.addEventListener('click', (e) => {
                    // 只有点击遮罩层本身时才关闭（不包括弹窗内容）
                    if (e.target === this.errorOverlay) {
                        this.closeErrorModal();
                    }
                });
            }
            
            // 键盘事件
            document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        }
        
        /**
         * 显示错误弹窗
         */
        showErrorModal() {
            if (this.errorModal) {
                // 添加显示动画
                this.errorModal.style.animation = 'slideInUp 0.4s ease';
                
                // 播放错误音效（如果有）
                this.playErrorSound();
            }
        }
        
        /**
         * 关闭错误弹窗
         */
        closeErrorModal() {
            if (this.errorModal) {
                // 添加关闭动画
                this.errorModal.style.animation = 'slideOutDown 0.3s ease';
                
                // 延迟导航
                setTimeout(() => {
                    this.navigateBack();
                }, 300);
            } else {
                // 如果没有动画，直接导航
                this.navigateBack();
            }
        }
        
        /**
         * 确认错误
         */
        confirmError() {
            // 记录用户确认
            this.logUserAction('confirmed');
            
            // 关闭弹窗
            this.closeErrorModal();
        }
        
        /**
         * 导航返回
         */
        navigateBack() {
            // 从URL参数获取返回地址
            const urlParams = new URLSearchParams(window.location.search);
            const returnUrl = urlParams.get('return') || urlParams.get('from');
            
            if (window.VivoEduApp) {
                // 使用应用路由
                if (returnUrl) {
                    window.VivoEduApp.navigateTo(returnUrl);
                } else {
                    window.VivoEduApp.navigateBack();
                }
            } else {
                // 使用浏览器导航
                if (returnUrl) {
                    window.location.href = returnUrl;
                } else if (window.history.length > 1) {
                    window.history.back();
                } else {
                    window.location.href = 'login.html';
                }
            }
        }
        
        /**
         * 处理键盘事件
         */
        handleKeyPress(e) {
            switch(e.key) {
                case 'Escape':
                    e.preventDefault();
                    this.closeErrorModal();
                    break;
                case 'Enter':
                    if (e.target.closest('.error-modal')) {
                        e.preventDefault();
                        this.confirmError();
                    }
                    break;
            }
        }
        
        /**
         * 播放错误音效
         */
        playErrorSound() {
            try {
                // 使用Web Audio API播放简单的错误音效
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.setValueAtTime(400, audioContext.currentTime);
                oscillator.frequency.setValueAtTime(200, audioContext.currentTime + 0.1);
                
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.2);
            } catch (error) {
                // 忽略音频播放错误
                console.log('音频播放失败:', error);
            }
        }
        
        /**
         * 设置初始焦点
         */
        setInitialFocus() {
            if (this.errorConfirm) {
                // 延迟设置焦点，等待动画完成
                setTimeout(() => {
                    this.errorConfirm.focus();
                }, 500);
            }
        }
        
        /**
         * 记录错误信息
         */
        logErrorInfo() {
            const errorInfo = {
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                url: window.location.href,
                referrer: document.referrer,
                errorType: 'unsupported_feature',
                message: '暂不支持'
            };
            
            // 记录到本地存储
            try {
                const errorLogs = JSON.parse(localStorage.getItem('errorLogs') || '[]');
                errorLogs.push(errorInfo);
                
                // 只保留最近50条记录
                if (errorLogs.length > 50) {
                    errorLogs.splice(0, errorLogs.length - 50);
                }
                
                localStorage.setItem('errorLogs', JSON.stringify(errorLogs));
            } catch (error) {
                console.error('记录错误信息失败:', error);
            }
            
            // 发送到后端（如果有配置）
            if (window.VivoEduApp && window.VivoEduApp.config.errorReporting) {
                this.sendErrorReport(errorInfo);
            }
        }
        
        /**
         * 记录用户操作
         */
        logUserAction(action) {
            const actionInfo = {
                timestamp: new Date().toISOString(),
                action: action,
                page: 'error',
                url: window.location.href
            };
            
            try {
                const actionLogs = JSON.parse(localStorage.getItem('actionLogs') || '[]');
                actionLogs.push(actionInfo);
                
                // 只保留最近100条记录
                if (actionLogs.length > 100) {
                    actionLogs.splice(0, actionLogs.length - 100);
                }
                
                localStorage.setItem('actionLogs', JSON.stringify(actionLogs));
            } catch (error) {
                console.error('记录用户操作失败:', error);
            }
        }
        
        /**
         * 发送错误报告
         */
        async sendErrorReport(errorInfo) {
            try {
                // 模拟发送错误报告到后端
                const response = await fetch('/api/error-report', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(errorInfo)
                });
                
                if (response.ok) {
                    console.log('错误报告已发送');
                } else {
                    console.error('发送错误报告失败:', response.status);
                }
            } catch (error) {
                console.error('发送错误报告异常:', error);
            }
        }
        
        /**
         * 获取错误类型
         */
        getErrorType() {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get('type') || 'general';
        }
        
        /**
         * 获取错误消息
         */
        getErrorMessage() {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get('message') || '暂不支持';
        }
        
        /**
         * 更新错误内容
         */
        updateErrorContent() {
            const errorType = this.getErrorType();
            const errorMessage = this.getErrorMessage();
            
            const errorTitle = document.querySelector('.error-title');
            const errorDescription = document.querySelector('.error-description');
            
            if (errorTitle) {
                errorTitle.textContent = this.getErrorTitle(errorType);
            }
            
            if (errorDescription) {
                errorDescription.textContent = this.getErrorDescription(errorType, errorMessage);
            }
        }
        
        /**
         * 获取错误标题
         */
        getErrorTitle(errorType) {
            const titles = {
                'unsupported': '暂不支持',
                'maintenance': '系统维护',
                'network': '网络错误',
                'permission': '权限不足',
                'general': '操作失败'
            };
            
            return titles[errorType] || '暂不支持';
        }
        
        /**
         * 获取错误描述
         */
        getErrorDescription(errorType, message) {
            const descriptions = {
                'unsupported': '该功能暂时无法使用，请稍后再试或联系管理员',
                'maintenance': '系统正在维护中，请稍后再试',
                'network': '网络连接异常，请检查网络设置后重试',
                'permission': '您没有权限访问此功能，请联系管理员',
                'general': '操作失败，请稍后重试'
            };
            
            return message || descriptions[errorType] || '该功能暂时无法使用，请稍后再试或联系管理员';
        }
    }
    
    // 页面加载完成后初始化
    document.addEventListener('DOMContentLoaded', () => {
        new ErrorPage();
    });
    
    // 导出到全局作用域
    window.ErrorPage = ErrorPage;
})(); 