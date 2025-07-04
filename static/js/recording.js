document.addEventListener('DOMContentLoaded', function() {
    // 获取元素
    const recordButton = document.querySelector('.image-6'); // 暂停/开始按钮
    const uploadButton = document.querySelector('.primary'); // 上传按钮
    
    let mediaRecorder;
    let chunks = [];
    let isRecording = false;
    let recordedAudio = null; // 存储录制的音频
    let stream = null; // 保存媒体流
    let isInitialized = false; // 标记是否已初始化

    // 初始化/请求权限函数
    async function requestPermissionsAndInit() {
        if (isInitialized) return true; // 如果已初始化，直接返回
        try {
            console.log("尝试获取麦克风权限...");
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = function(e) {
                chunks.push(e.data);
            };

            mediaRecorder.onstop = function() {
                const blob = new Blob(chunks, { 'type': 'audio/webm; codecs=opus' });
                chunks = [];
                recordedAudio = new File([blob], `recording_${Date.now()}.webm`, { type: 'audio/webm' });
                // 启用上传按钮
                uploadButton.style.opacity = '1';
                uploadButton.style.cursor = 'pointer';
                console.log("录音停止，文件已准备好");
            };

            isInitialized = true; // 标记为已初始化
            console.log("麦克风权限获取成功并初始化MediaRecorder");
            return true;
        } catch (err) {
            console.error('麦克风访问错误:', err);
            let message = '无法访问麦克风。';
            if (err.name === 'NotAllowedError') {
                message += ' 您可能拒绝了权限请求，请检查浏览器和系统设置。';
            } else if (err.name === 'NotFoundError') {
                message += ' 未找到可用的麦克风设备。';
            } else if (err.name === 'SecurityError' || location.protocol !== 'https:'){
                 message += ' 访问麦克风需要安全的HTTPS连接。';
            } else {
                 message += ' 请检查设备和浏览器设置。';
            }
            alert(message);
            isInitialized = false;
            return false;
        }
    }

    // 显示自定义名称模态框
    function showCustomNameModal() {
        const customNameModal = new bootstrap.Modal(document.getElementById('customNameModal'));
        customNameModal.show();
    }

    // 处理录音按钮点击
    if (recordButton) {
        recordButton.addEventListener('click', async function() {
            if (!isRecording) {
                // 先确保初始化和权限
                const ready = await requestPermissionsAndInit();
                if (!ready || !mediaRecorder) {
                    console.log('录音未准备好或无权限');
                    return; // 如果初始化失败或 mediaRecorder 仍未定义，则不继续
                }

                // 开始录音
                chunks = []; // 清空之前的录音数据
                try {
                    mediaRecorder.start();
                    isRecording = true;
                    recordButton.src = "../static/icon/暂停.svg"; // 应该显示暂停图标
                    console.log('录音开始');
                    showToast('录音开始', 'start');
                    // 禁用上传按钮
                    uploadButton.style.opacity = '0.5';
                    uploadButton.style.cursor = 'not-allowed';
                } catch (error) {
                    console.error("启动录音失败:", error);
                    alert("启动录音失败，请重试。");
                    isRecording = false; // 确保状态正确
                    recordButton.src = "../static/icon/开始.svg"; // 恢复开始图标
                }
            } else {
                // 停止录音
                if (mediaRecorder && mediaRecorder.state === 'recording') { // 确保在录音状态
                   mediaRecorder.stop();
                   console.log('录音停止');
                   isRecording = false;
                   recordButton.src = "../static/icon/开始.svg"; // 应该显示开始图标
                   showToast('录音结束', 'stop');
                } else {
                     console.warn("MediaRecorder 不在录音状态，无法停止");
                }
            }
        });
    }

    // 处理上传按钮点击
    if (uploadButton) {
        uploadButton.addEventListener('click', function() {
            if (!recordedAudio) {
                alert('请先录制音频');
                return;
            }
            if (isRecording) {
                alert('请先停止录音');
                return;
            }
            // 显示模态框
            showCustomNameModal();
        });
    }

    // 处理自定义名称表单提交
    const customNameForm = document.getElementById('custom-name-form');
    if (customNameForm) {
        customNameForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const childName = document.getElementById('child-name').value.trim();
            const date = document.getElementById('date').value;
            if (!childName || !date) {
                alert('请填写所有字段。');
                return;
            }
            const customName = `${childName}_${date}`;
            // 隐藏模态框
            const customNameModal = bootstrap.Modal.getInstance(document.getElementById('customNameModal'));
            customNameModal.hide();
            // 上传录音
            uploadRecordedAudio(customName);
        });
    }

    // 上传录音文件
    async function uploadRecordedAudio(customName) {
        const token = localStorage.getItem('jwtToken');
        if (!token) {
            alert('用户未登录');
            window.location.href = '/login';
            return;
        }

        try {
            // 获取上传URL
            const urlResponse = await axios.post('/api/audio/get_upload_url', {
                file_name: recordedAudio.name,
                custom_name: customName
            }, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (urlResponse.data.code !== 200) {
                throw new Error(urlResponse.data.msg || '获取上传URL失败');
            }

            const { upload_url } = urlResponse.data.data;

            // 上传文件
            const formData = new FormData();
            formData.append('file', recordedAudio);

            const uploadResponse = await axios.post(upload_url, formData, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                }
            });

            if (uploadResponse.data.code === 200) {
                alert('录音上传成功');
                window.location.href = '/home_page'; // 修改为正确的主页路径
            } else {
                throw new Error(uploadResponse.data.msg || '上传失败');
            }
        } catch (error) {
            console.error('上传失败:', error);
            alert('上传失败：' + (error.response?.data?.msg || error.message));
        }
    }

    // 检查登录状态
    function checkLoginStatus() {
        const token = localStorage.getItem('jwtToken');
        if (!token) {
            window.location.href = '/login';
        }
    }

    // 初始化
    checkLoginStatus();
    requestPermissionsAndInit();
    
    // 初始时禁用上传按钮
    uploadButton.style.opacity = '0.5';
    uploadButton.style.cursor = 'not-allowed';

    // 添加显示提示的函数
    function showToast(message, type) {
        // 创建或获取 toast 元素
        let toast = document.querySelector('.recording-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.className = 'recording-toast';
            document.body.appendChild(toast);
        }
        
        // 设置提示内容和类型
        toast.textContent = message;
        toast.className = `recording-toast show ${type}`;
        
        // 2秒后自动隐藏
        setTimeout(() => {
            toast.className = 'recording-toast';
        }, 2000);
    }
});
