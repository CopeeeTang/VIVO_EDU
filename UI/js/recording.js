/**
 * 录音页面JavaScript功能
 * 处理录音状态切换、音频录制、波形可视化、权限管理等功能
 */

(function() {
    'use strict';
    
    // 录音页面类
    class RecordingPage {
        constructor() {
            // DOM 元素
            this.backBtn = document.getElementById('backBtn');
            this.prepareState = document.getElementById('prepareState');
            this.recordingStateContent = document.getElementById('recordingStateContent');
            this.finishedState = document.getElementById('finishedState');
            this.recordingTime = document.getElementById('recordingTime');
            this.timeDisplay = document.querySelector('.time-display');
            this.prepareControls = document.getElementById('prepareControls');
            this.recordingControlsSection = document.getElementById('recordingControlsSection');
            this.finishedControls = document.getElementById('finishedControls');
            this.startRecordBtn = document.getElementById('startRecordBtn');
            this.stopRecordBtn = document.getElementById('stopRecordBtn');
            this.cancelBtn = document.getElementById('cancelBtn');
            this.uploadBtn = document.getElementById('uploadBtn');
            this.permissionModal = document.getElementById('permissionModal');
            this.permissionCancel = document.getElementById('permissionCancel');
            this.permissionConfirm = document.getElementById('permissionConfirm');
            this.recordingTips = document.getElementById('recordingTips');
            this.audioVisualizer = document.getElementById('audioVisualizer');
            
            // 录音相关属性
            this.mediaRecorder = null;
            this.audioChunks = [];
            this.audioBlob = null;
            this.isRecording = false;
            this.recordingStartTime = null;
            this.recordingTimer = null;
            this.currentState = 'prepare'; // prepare, recording, finished
            
            // 波形可视化
            this.audioContext = null;
            this.analyser = null;
            this.dataArray = null;
            this.animationFrame = null;
            
            // 初始化
            this.init();
        }
        
        /**
         * 初始化
         */
        init() {
            // 绑定事件
            this.bindEvents();
            
            // 初始化状态
            this.setState('prepare');
            
            // 显示录音提示
            setTimeout(() => {
                this.showRecordingTips();
            }, 1000);
        }
        
        /**
         * 绑定事件
         */
        bindEvents() {
            // 返回按钮
            if (this.backBtn) {
                this.backBtn.addEventListener('click', () => this.handleBack());
            }
            
            // 开始录音
            if (this.startRecordBtn) {
                this.startRecordBtn.addEventListener('click', () => this.startRecording());
            }
            
            // 停止录音
            if (this.stopRecordBtn) {
                this.stopRecordBtn.addEventListener('click', () => this.stopRecording());
            }
            
            // 取消录音
            if (this.cancelBtn) {
                this.cancelBtn.addEventListener('click', () => this.cancelRecording());
            }
            
            // 上传录音
            if (this.uploadBtn) {
                this.uploadBtn.addEventListener('click', () => this.uploadRecording());
            }
            
            // 权限弹窗
            if (this.permissionCancel) {
                this.permissionCancel.addEventListener('click', () => this.hidePermissionModal());
            }
            
            if (this.permissionConfirm) {
                this.permissionConfirm.addEventListener('click', () => this.requestPermission());
            }
            
            // 点击遮罩关闭弹窗
            if (this.permissionModal) {
                this.permissionModal.addEventListener('click', (e) => {
                    if (e.target === this.permissionModal || e.target.classList.contains('modal-overlay')) {
                        this.hidePermissionModal();
                    }
                });
            }
            
            // 键盘事件
            document.addEventListener('keydown', (e) => this.handleKeydown(e));
        }
        
        /**
         * 设置录音状态
         */
        setState(state) {
            this.currentState = state;
            
            // 隐藏所有状态
            this.prepareState?.classList.remove('active');
            this.recordingStateContent?.classList.remove('active');
            this.finishedState?.classList.remove('active');
            this.prepareControls?.classList.remove('active');
            this.recordingControlsSection?.classList.remove('active');
            this.finishedControls?.classList.remove('active');
            
            // 显示对应状态
            switch(state) {
                case 'prepare':
                    this.prepareState?.classList.add('active');
                    this.prepareControls?.classList.add('active');
                    this.recordingTime?.classList.remove('active');
                    this.hideRecordingTips();
                    break;
                case 'recording':
                    this.recordingStateContent?.classList.add('active');
                    this.recordingControlsSection?.classList.add('active');
                    this.recordingTime?.classList.add('active');
                    this.hideRecordingTips();
                    break;
                case 'finished':
                    this.finishedState?.classList.add('active');
                    this.finishedControls?.classList.add('active');
                    this.recordingTime?.classList.remove('active');
                    this.hideRecordingTips();
                    break;
            }
        }
        
        /**
         * 开始录音
         */
        async startRecording() {
            try {
                // 检查浏览器支持
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    this.showError('您的浏览器不支持录音功能');
                    return;
                }
                
                // 请求麦克风权限
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    } 
                });
                
                // 初始化录音器
                this.mediaRecorder = new MediaRecorder(stream);
                this.audioChunks = [];
                
                // 设置录音事件
                this.mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        this.audioChunks.push(event.data);
                    }
                };
                
                this.mediaRecorder.onstop = () => {
                    this.audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                    this.setState('finished');
                    
                    // 停止音频流
                    stream.getTracks().forEach(track => track.stop());
                    
                    // 停止波形可视化
                    this.stopVisualization();
                };
                
                // 开始录音
                this.mediaRecorder.start();
                this.isRecording = true;
                this.recordingStartTime = Date.now();
                
                // 切换到录音状态
                this.setState('recording');
                
                // 开始计时
                this.startTimer();
                
                // 开始波形可视化
                this.startVisualization(stream);
                
                console.log('录音开始');
                
            } catch (error) {
                console.error('录音启动失败:', error);
                
                if (error.name === 'NotAllowedError') {
                    this.showPermissionModal();
                } else if (error.name === 'NotFoundError') {
                    this.showError('未找到麦克风设备');
                } else {
                    this.showError('录音功能启动失败，请检查设备权限');
                }
            }
        }
        
        /**
         * 停止录音
         */
        stopRecording() {
            if (this.mediaRecorder && this.isRecording) {
                this.mediaRecorder.stop();
                this.isRecording = false;
                
                // 停止计时
                this.stopTimer();
                
                console.log('录音停止');
            }
        }
        
        /**
         * 取消录音
         */
        cancelRecording() {
            // 清理录音数据
            this.audioChunks = [];
            this.audioBlob = null;
            
            // 重置状态
            this.setState('prepare');
            this.resetTimer();
            
            console.log('录音已取消');
        }
        
        /**
         * 上传录音
         */
        async uploadRecording() {
            if (!this.audioBlob) {
                this.showError('没有录音数据可上传');
                return;
            }
            
            try {
                // 显示上传状态
                const uploadBtn = this.uploadBtn;
                const originalText = uploadBtn.querySelector('.btn-text').textContent;
                uploadBtn.querySelector('.btn-text').textContent = '上传中...';
                uploadBtn.disabled = true;
                
                // 创建表单数据
                const formData = new FormData();
                formData.append('audio', this.audioBlob, `recording_${Date.now()}.wav`);
                formData.append('duration', this.getRecordingDuration());
                formData.append('timestamp', this.recordingStartTime);
                
                // 模拟上传过程
                await this.simulateUpload(formData);
                
                // 上传成功
                console.log('录音上传成功');
                
                // 跳转到处理页面或返回主页
                if (window.VivoEduApp) {
                    window.VivoEduApp.navigateTo('home.html');
                } else {
                    window.location.href = 'home.html';
                }
                
            } catch (error) {
                console.error('录音上传失败:', error);
                this.showError('录音上传失败，请重试');
                
                // 恢复按钮状态
                const uploadBtn = this.uploadBtn;
                uploadBtn.querySelector('.btn-text').textContent = originalText;
                uploadBtn.disabled = false;
            }
        }
        
        /**
         * 模拟上传过程
         */
        async simulateUpload(formData) {
            return new Promise((resolve, reject) => {
                // 模拟网络延迟
                setTimeout(() => {
                    // 这里应该调用实际的上传API
                    // const response = await fetch('/api/upload-recording', {
                    //     method: 'POST',
                    //     body: formData
                    // });
                    
                    // 模拟成功
                    if (Math.random() > 0.1) { // 90% 成功率
                        resolve({ success: true });
                    } else {
                        reject(new Error('网络错误'));
                    }
                }, 2000);
            });
        }
        
        /**
         * 开始计时
         */
        startTimer() {
            this.recordingTimer = setInterval(() => {
                if (this.recordingStartTime) {
                    const elapsed = Date.now() - this.recordingStartTime;
                    this.updateTimeDisplay(elapsed);
                }
            }, 1000);
        }
        
        /**
         * 停止计时
         */
        stopTimer() {
            if (this.recordingTimer) {
                clearInterval(this.recordingTimer);
                this.recordingTimer = null;
            }
        }
        
        /**
         * 重置计时
         */
        resetTimer() {
            this.stopTimer();
            this.recordingStartTime = null;
            this.updateTimeDisplay(0);
        }
        
        /**
         * 更新时间显示
         */
        updateTimeDisplay(elapsed) {
            const seconds = Math.floor(elapsed / 1000);
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            
            const timeString = `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
            if (this.timeDisplay) {
                this.timeDisplay.textContent = timeString;
            }
        }
        
        /**
         * 获取录音时长
         */
        getRecordingDuration() {
            if (this.recordingStartTime) {
                return Date.now() - this.recordingStartTime;
            }
            return 0;
        }
        
        /**
         * 开始波形可视化
         */
        startVisualization(stream) {
            try {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                this.analyser = this.audioContext.createAnalyser();
                const source = this.audioContext.createMediaStreamSource(stream);
                
                source.connect(this.analyser);
                this.analyser.fftSize = 256;
                
                const bufferLength = this.analyser.frequencyBinCount;
                this.dataArray = new Uint8Array(bufferLength);
                
                this.animateWaveform();
            } catch (error) {
                console.error('波形可视化启动失败:', error);
            }
        }
        
        /**
         * 停止波形可视化
         */
        stopVisualization() {
            if (this.animationFrame) {
                cancelAnimationFrame(this.animationFrame);
                this.animationFrame = null;
            }
            
            if (this.audioContext) {
                this.audioContext.close();
                this.audioContext = null;
            }
        }
        
        /**
         * 动画波形
         */
        animateWaveform() {
            if (!this.analyser || !this.dataArray) return;
            
            this.animationFrame = requestAnimationFrame(() => this.animateWaveform());
            
            this.analyser.getByteFrequencyData(this.dataArray);
            
            // 更新SVG波形
            this.updateWaveformSVG(this.dataArray);
        }
        
        /**
         * 更新波形SVG
         */
        updateWaveformSVG(dataArray) {
            if (!this.audioVisualizer) return;
            
            const rects = this.audioVisualizer.querySelectorAll('rect');
            const step = Math.floor(dataArray.length / rects.length);
            
            rects.forEach((rect, index) => {
                const value = dataArray[index * step] || 0;
                const height = Math.max(3, (value / 255) * 20);
                const y = (23 - height) / 2;
                
                rect.setAttribute('height', height);
                rect.setAttribute('y', y);
                
                // 添加颜色变化
                const opacity = 0.3 + (value / 255) * 0.7;
                rect.style.opacity = opacity;
            });
        }
        
        /**
         * 显示权限弹窗
         */
        showPermissionModal() {
            this.permissionModal?.classList.add('active');
        }
        
        /**
         * 隐藏权限弹窗
         */
        hidePermissionModal() {
            this.permissionModal?.classList.remove('active');
        }
        
        /**
         * 请求权限
         */
        async requestPermission() {
            this.hidePermissionModal();
            
            try {
                await navigator.mediaDevices.getUserMedia({ audio: true });
                // 权限获取成功，开始录音
                this.startRecording();
            } catch (error) {
                console.error('权限请求失败:', error);
                this.showError('无法获取麦克风权限，请在浏览器设置中允许录音权限');
            }
        }
        
        /**
         * 显示录音提示
         */
        showRecordingTips() {
            this.recordingTips?.classList.add('active');
            
            // 3秒后自动隐藏
            setTimeout(() => {
                this.hideRecordingTips();
            }, 3000);
        }
        
        /**
         * 隐藏录音提示
         */
        hideRecordingTips() {
            this.recordingTips?.classList.remove('active');
        }
        
        /**
         * 显示错误消息
         */
        showError(message) {
            // 简单的错误提示，实际项目中应该使用更好的UI
            alert(message);
        }
        
        /**
         * 处理返回按钮
         */
        handleBack() {
            if (this.isRecording) {
                const confirmed = confirm('正在录音中，确定要退出吗？');
                if (!confirmed) return;
                
                // 停止录音
                this.stopRecording();
            }
            
            // 清理资源
            this.cleanup();
            
            // 返回上一页
            if (window.VivoEduApp) {
                window.VivoEduApp.navigateTo('home.html');
            } else {
                window.history.back();
            }
        }
        
        /**
         * 处理键盘事件
         */
        handleKeydown(e) {
            switch(e.key) {
                case 'Escape':
                    if (this.permissionModal?.classList.contains('active')) {
                        this.hidePermissionModal();
                    } else {
                        this.handleBack();
                    }
                    break;
                case ' ':
                case 'Enter':
                    e.preventDefault();
                    if (this.currentState === 'prepare') {
                        this.startRecording();
                    } else if (this.currentState === 'recording') {
                        this.stopRecording();
                    }
                    break;
            }
        }
        
        /**
         * 清理资源
         */
        cleanup() {
            this.stopTimer();
            this.stopVisualization();
            
            if (this.mediaRecorder && this.isRecording) {
                this.mediaRecorder.stop();
            }
        }
        
        /**
         * 获取录音数据
         */
        getRecordingData() {
            return {
                blob: this.audioBlob,
                duration: this.getRecordingDuration(),
                timestamp: this.recordingStartTime
            };
        }
        
        /**
         * 播放录音
         */
        playRecording() {
            if (!this.audioBlob) return;
            
            const audio = new Audio(URL.createObjectURL(this.audioBlob));
            audio.play().catch(error => {
                console.error('播放失败:', error);
                this.showError('录音播放失败');
            });
        }
    }
    
    // 页面加载完成后初始化
    document.addEventListener('DOMContentLoaded', () => {
        const recordingPage = new RecordingPage();
        
        // 导出到全局作用域，供其他脚本使用
        window.RecordingPage = recordingPage;
        
        // 页面卸载时清理资源
        window.addEventListener('beforeunload', () => {
            recordingPage.cleanup();
        });
    });
    
    // 导出类
    window.RecordingPageClass = RecordingPage;
})(); 