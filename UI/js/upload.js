/**
 * 文件上传页面功能
 */
class UploadPage {
    constructor() {
        this.selectedFiles = [];
        this.isUploading = false;
        this.uploadProgress = 0;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateButtonStates();
    }

    bindEvents() {
        // 文件选择
        const fileInput = document.getElementById('fileInput');
        const uploadZone = document.getElementById('uploadZone');
        
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }
        
        if (uploadZone) {
            uploadZone.addEventListener('click', () => this.triggerFileSelect());
            uploadZone.addEventListener('dragover', (e) => this.handleDragOver(e));
            uploadZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            uploadZone.addEventListener('drop', (e) => this.handleDrop(e));
        }
    }

    triggerFileSelect() {
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.click();
        }
    }

    handleFileSelect(event) {
        const files = Array.from(event.target.files);
        this.addFiles(files);
    }

    handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        
        const uploadZone = document.getElementById('uploadZone');
        if (uploadZone) {
            uploadZone.classList.add('drag-over');
        }
    }

    handleDragLeave(event) {
        event.preventDefault();
        event.stopPropagation();
        
        const uploadZone = document.getElementById('uploadZone');
        if (uploadZone) {
            uploadZone.classList.remove('drag-over');
        }
    }

    handleDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        
        const uploadZone = document.getElementById('uploadZone');
        if (uploadZone) {
            uploadZone.classList.remove('drag-over');
        }
        
        const files = Array.from(event.dataTransfer.files);
        this.addFiles(files);
    }

    addFiles(files) {
        const validFiles = files.filter(file => this.isValidFile(file));
        
        if (validFiles.length === 0) {
            this.showError('请选择有效的音频文件（MP3、WAV、M4A格式）');
            return;
        }
        
        // 检查文件大小
        const oversizedFiles = validFiles.filter(file => file.size > 100 * 1024 * 1024);
        if (oversizedFiles.length > 0) {
            this.showError(`以下文件超过100MB限制：${oversizedFiles.map(f => f.name).join(', ')}`);
            return;
        }
        
        // 添加文件到列表
        validFiles.forEach(file => {
            if (!this.selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
                this.selectedFiles.push(file);
            }
        });
        
        this.updateFileList();
        this.updateButtonStates();
    }

    isValidFile(file) {
        const validTypes = [
            'audio/mp3',
            'audio/mpeg',
            'audio/wav',
            'audio/x-wav',
            'audio/wave',
            'audio/mp4',
            'audio/m4a',
            'audio/x-m4a'
        ];
        
        const validExtensions = ['.mp3', '.wav', '.m4a'];
        const hasValidType = validTypes.includes(file.type);
        const hasValidExtension = validExtensions.some(ext => 
            file.name.toLowerCase().endsWith(ext)
        );
        
        return hasValidType || hasValidExtension;
    }

    updateFileList() {
        const fileList = document.getElementById('fileList');
        const fileItems = document.getElementById('fileItems');
        
        if (!fileList || !fileItems) return;
        
        if (this.selectedFiles.length === 0) {
            fileList.style.display = 'none';
            return;
        }
        
        fileList.style.display = 'block';
        fileItems.innerHTML = '';
        
        this.selectedFiles.forEach((file, index) => {
            const fileItem = this.createFileItem(file, index);
            fileItems.appendChild(fileItem);
        });
    }

    createFileItem(file, index) {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <div class="file-icon">
                ${this.getFileIcon(file)}
            </div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-meta">
                    ${this.formatFileSize(file.size)} • ${this.getFileType(file)}
                </div>
            </div>
            <div class="file-actions">
                <button class="file-action-btn remove" onclick="UploadPage.removeFile(${index})">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                </button>
            </div>
        `;
        
        return item;
    }

    getFileIcon(file) {
        const name = file.name.toLowerCase();
        if (name.endsWith('.mp3')) return 'MP3';
        if (name.endsWith('.wav')) return 'WAV';
        if (name.endsWith('.m4a')) return 'M4A';
        return 'AUD';
    }

    getFileType(file) {
        const name = file.name.toLowerCase();
        if (name.endsWith('.mp3')) return 'MP3 音频';
        if (name.endsWith('.wav')) return 'WAV 音频';
        if (name.endsWith('.m4a')) return 'M4A 音频';
        return '音频文件';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.updateFileList();
        this.updateButtonStates();
    }

    clearFiles() {
        this.selectedFiles = [];
        this.updateFileList();
        this.updateButtonStates();
        
        // 清空文件输入
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.value = '';
        }
    }

    updateButtonStates() {
        const clearButton = document.getElementById('clearButton');
        const uploadButton = document.getElementById('uploadButton');
        
        const hasFiles = this.selectedFiles.length > 0;
        
        if (clearButton) {
            clearButton.disabled = !hasFiles || this.isUploading;
        }
        
        if (uploadButton) {
            uploadButton.disabled = !hasFiles || this.isUploading;
        }
    }

    startUpload() {
        if (this.selectedFiles.length === 0 || this.isUploading) {
            return;
        }
        
        this.isUploading = true;
        this.updateButtonStates();
        
        // 显示进度条
        const progressContainer = document.getElementById('uploadProgress');
        if (progressContainer) {
            progressContainer.style.display = 'block';
        }
        
        // 模拟上传过程
        this.simulateUpload();
    }

    simulateUpload() {
        const totalFiles = this.selectedFiles.length;
        let completedFiles = 0;
        let progress = 0;
        
        const updateProgress = () => {
            progress += Math.random() * 15;
            
            if (progress >= 100) {
                progress = 100;
                completedFiles = totalFiles;
                this.finishUpload();
            } else {
                this.updateProgress(progress);
                setTimeout(updateProgress, 500 + Math.random() * 1000);
            }
        };
        
        updateProgress();
    }

    updateProgress(progress) {
        const progressFill = document.getElementById('progressFill');
        const progressPercentage = document.getElementById('progressPercentage');
        const uploadSpeed = document.getElementById('uploadSpeed');
        const remainingTime = document.getElementById('remainingTime');
        
        if (progressFill) {
            progressFill.style.width = progress + '%';
        }
        
        if (progressPercentage) {
            progressPercentage.textContent = Math.round(progress) + '%';
        }
        
        if (uploadSpeed) {
            uploadSpeed.textContent = (Math.random() * 2000 + 500).toFixed(0) + ' KB/s';
        }
        
        if (remainingTime) {
            const remaining = Math.round((100 - progress) / 10);
            remainingTime.textContent = remaining > 0 ? remaining + ' 秒' : '即将完成';
        }
    }

    finishUpload() {
        this.isUploading = false;
        
        // 隐藏进度条
        const progressContainer = document.getElementById('uploadProgress');
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
        
        // 显示成功消息
        this.showSuccess('文件上传成功！AI正在分析处理中...');
        
        // 清空文件列表
        setTimeout(() => {
            this.clearFiles();
            
            // 根据设置决定是否跳转
            const autoAnalysis = document.getElementById('autoAnalysis');
            if (autoAnalysis && autoAnalysis.checked) {
                setTimeout(() => {
                    App.navigateTo('history');
                }, 2000);
            }
        }, 1500);
    }

    showSuccess(message) {
        // 简单的成功提示
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #4CAF50;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            font-weight: 500;
        `;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    showError(message) {
        // 简单的错误提示
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #f87171;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            font-weight: 500;
        `;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// 静态方法供HTML调用
UploadPage.removeFile = function(index) {
    if (window.uploadPageInstance) {
        window.uploadPageInstance.removeFile(index);
    }
};

UploadPage.clearFiles = function() {
    if (window.uploadPageInstance) {
        window.uploadPageInstance.clearFiles();
    }
};

UploadPage.startUpload = function() {
    if (window.uploadPageInstance) {
        window.uploadPageInstance.startUpload();
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.uploadPageInstance = new UploadPage();
});

// 防止页面意外拖拽
document.addEventListener('dragover', (e) => {
    e.preventDefault();
});

document.addEventListener('drop', (e) => {
    e.preventDefault();
}); 