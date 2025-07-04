document.addEventListener('DOMContentLoaded', function() {
    // 获取元素
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    let selectedFile = null;

    // 点击上传按钮时触发文件选择
    uploadBtn.addEventListener('click', function() {
        fileInput.click();
    });

    // 监听文件选择
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            showCustomNameModal();
        }
    });

    // 显示自定义名称模态框
    function showCustomNameModal() {
        const customNameModal = new bootstrap.Modal(document.getElementById('customNameModal'), {
            backdrop: 'static',
            keyboard: false
        });
        customNameModal.show();
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
            // 上传文件
            uploadFile(selectedFile, customName);
        });
    }

    // 上传文件函数
    async function uploadFile(file, customName) {
        const token = localStorage.getItem('jwtToken');
        if (!token) {
            alert('用户未登录');
            window.location.href = '/login';
            return;
        }

        try {
            // 获取上传URL
            const urlResponse = await axios.post('/api/audio/get_upload_url', {
                file_name: file.name,
                custom_name: customName,
            }, {
                headers: { 'Authorization': `Bearer ${token}` }
            });


            if (urlResponse.data.code !== 200) {
                throw new Error(urlResponse.data.msg || '获取上传URL失败');
            }

            const { upload_url } = urlResponse.data.data;

            // 上传文件
            const formData = new FormData();
            formData.append('file', file);

            const uploadResponse = await axios.post(upload_url, formData, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                }
            });

            if (uploadResponse.data.code === 200) {
                alert('文件上传成功');
                window.location.href = '/home_page'; // 返回主页
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
});
