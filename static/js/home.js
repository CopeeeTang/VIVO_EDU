// home.js

document.addEventListener('DOMContentLoaded', function() {
    // 获取报告列表
    function fetchReportList() {
        const token = localStorage.getItem('jwtToken');
        axios.get('/api/audio/list_files', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (response.data.code === 200) {
                const files = response.data.data.files;
                renderReportList(files);
            }
        })
        .catch(error => {
            if (error.response) {
                if (error.response.status === 401) {
                    alert('登录已过期，请重新登录');
                    window.location.href = '/login';
                } else {
                    console.error('获取报告列表失败:', error);
                }
            } else {
                console.error('获取报告列表失败:', error);
            }
        });
    }
    /**
     * 统一处理认证错误
     * @param {Object} error - Axios 错误对象
     */
    function handleAuthError(error) {
        if (error.response) {
            const status = error.response.status;
            const msg = error.response.data.msg || '';

            if (status === 401 || (status === 500 && msg.includes('Signature has expired'))) {
                alert('登录已过期，请重新登录。');
                window.location.href = '/login';
            } else {
                // 处理其他错误
                alert(`错误: ${msg || '发生未知错误。'}`);
            }
        } else {
            alert('网络连接异常，请检查后重试。');
        }
    }

    // 添加长按事件处理
    let pressTimer;
    const longPressDuration = 800; // 长按时间阈值（毫秒）

    // 渲染报告列表
    function renderReportList(files) {
        const frame = document.querySelector('.frame');
        frame.innerHTML = ''; // 清空现有内容

        if (files.length === 0) {
            // 如果没有文件，显示提示信息
            frame.innerHTML = '<div class="no-reports">暂无分析报告</div>';
            return;
        }

        files.forEach(file => {
            // 格式化音频时长
            const duration = file.duration ? formatDuration(file.duration) : '00:00';
            
            const reportHTML = `
                <div class="group" data-file-id="${file.file_id}">
                    <div class="overlap-group">
                        <div class="rectangle"></div>
                        <div class="text-wrapper-2">${file.custom_name || file.file_name}</div>
                        <div class="rectangle-2"></div>
                        <img class="icon" src="static/icon/boy.png" />
                        <div class="group-2"></div>
                        <div class="group-3"></div>
                        <img class="vector" src="https://c.animaapp.com/lzvVI57f/img/vector-9-5.svg" />
                        ${getActionButton(file)}
                    </div>
                </div>
            `;
            frame.insertAdjacentHTML('beforeend', reportHTML);

            // If the file is currently processing, start polling its progress immediately
            if (file.status === 'processing') {
                pollProgress(file.file_id);
            }
        });

        addEventListeners(); // 添加按钮事件监听器
        addLongPressListeners(); // 添加长按事件监听器
    }

    // 获取操作按钮的HTML
    function getActionButton(file) {
        let actionHTML = '';
        if (file.status === 'completed') {
            actionHTML = `<button class="action-btn view-report-btn" data-file-id="${file.file_id}">查看报告</button>`;
        } else if (file.status === 'pending' || file.status === 'failed') {
            actionHTML = `<button class="action-btn start-analysis-btn" data-file-id="${file.file_id}">开始分析</button>`;
        } else if (file.status === 'processing') {
            actionHTML = `
                <div class="progress-wrapper">
                    <div class="progress-container">
                        <div class="progress-bar" id="progress-bar-${file.file_id}"></div>
                    </div>
                    <div class="status-text" id="status-text-${file.file_id}">处理中...<br>0%</div>
                </div>
            `;
        }
        return `<div class="action-buttons">${actionHTML}</div>`;
    }

    // 格式化日期函数
    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day} ${hours}:${minutes}`;
    }

    // 查看报告函数
    async function viewReport(fileId) {
        try {
            console.log('开始查看报告,fileId:', fileId);
            const token = localStorage.getItem('jwtToken');
            
            // 1. 先调用 get_analysis 生成所有报告文件
            console.log('开始调用get_analysis接口');
            const analysisResponse = await fetch(`/api/audio/get_analysis/${fileId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            const analysisData = await analysisResponse.json();
            console.log('解析后的响应数据:', analysisData);
            
            if (analysisData.code === 200) {
                console.log('生成报告成功,准备跳转');
                const redirectPath = `/static/reports/output0_${fileId}.html`;
                console.log('跳转路径:', redirectPath);
                window.location.href = redirectPath;
            } else {
                console.error('生成报告失败:', analysisData.msg);
                alert('生成报告失败：' + analysisData.msg);
            }
        } catch (error) {
            console.error('生成报告时出错:', error);
            console.error('错误详情:', error.stack);
            alert('生成报告时出错，请稍后重试');
        }
    }

    // 启动分析任务函数
    function startAnalysis(fileId, row) {
        const token = localStorage.getItem('jwtToken');

        if (!token) {
            alert('用户未登录。');
            window.location.href = '/login';
            return;
        }

        axios.post(`/api/audio/analyze/${fileId}`, {}, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (response.data.code === 200) {
                // 更新状态为 processing
                updateRowToProcessing(fileId, row);

                // 开始轮询进度
                pollProgress(fileId);
            } else if (response.data.code === 400) {
                alert(response.data.msg);
            } else {
                alert('启动分析任务失败！');
            }
        })
        .catch(error => {
            handleAnalyzeError(error);
        });
    }

    // 更新行状态为 processing
    function updateRowToProcessing(fileId, row) {
        // 更新文件状态为 processing
        const file = { status: 'processing' };
        // 更新 UI
        const actionCell = row.querySelector('.action-buttons');
        if (actionCell) {
            actionCell.innerHTML = `
                <div class="progress-wrapper">
                    <div class="progress-container">
                        <div class="progress-bar" id="progress-bar-${fileId}"></div>
                    </div>
                    <div class="status-text" id="status-text-${fileId}">处理中...<br>0%</div>
                </div>
            `;
        }

        // 禁用删除按钮，防止分析过程中删除文件
        const deleteButton = row.querySelector('.delete-btn');
        if (deleteButton) {
            deleteButton.disabled = true;
        }
    }

    // 处理分析错误
    function handleAnalyzeError(error) {
        if (error.response) {
            if (error.response.status === 401) {
                alert('未授权访问，请重新登录！');
                window.location.href = '/login';
            } else if (error.response.status === 404) {
                alert('文件记录不存在！');
            } else if (error.response.status === 500) {
                alert(`服务器内部错误: ${error.response.data.msg}`);
            } else {
                alert(`启动分析任务失败：${error.response.data.msg}`);
            }
        } else {
            alert('启动分析任务时发生网络错误，请检查网络连接！');
        }
        console.error('启动分析任务错误:', error);
    }

    // 轮询任务进度函数
    function pollProgress(fileId) {
        const intervalId = setInterval(() => {
            axios.get(`/api/audio/progress/${fileId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('jwtToken')}`
                }
            })
            .then(response => {
                if (response.data.code === 200) {
                    const data = response.data.data;
                    const progressBar = document.getElementById(`progress-bar-${fileId}`);
                    const statusText = document.getElementById(`status-text-${fileId}`);

                    if (progressBar && statusText) {
                        const percent = Math.min((data.current / data.total) * 100, 100);
                        progressBar.style.width = `${percent}%`;
                        statusText.innerHTML = `${getStatusText(data.status)}<br>${percent}%`;

                        if (data.status === '已完成') {
                            clearInterval(intervalId);
                            statusText.textContent = '分析完成';
                            updateRowToCompleted(fileId);
                        } else if (data.status === '失败') {
                            clearInterval(intervalId);
                            statusText.textContent = `失败: ${data.error || '未知错误'}`;
                            updateRowToFailed(fileId);
                        }
                    }
                } else {
                    clearInterval(intervalId);
                    alert('获取进度信息失败！');
                }
            })
            .catch(error => {
                clearInterval(intervalId);
                alert('获取进度信息时发生错误！');
                console.error('获取进度错误:', error);
            });
        }, 2000);  // 每2秒轮询一次
    }

    // 更新行状态为 completed
    function updateRowToCompleted(fileId) {
        const row = document.querySelector(`.group[data-file-id="${fileId}"]`);
        if (row) {
            const actionCell = row.querySelector('.action-buttons');
            if (actionCell) {
                actionCell.innerHTML = `<button class="action-btn view-report-btn" data-file-id="${fileId}">查看报告</button>`;
                addEventListeners();  // 重新绑定事件监听器
            }

            // 重新启用删除按钮
            const deleteButton = row.querySelector('.delete-btn');
            if (deleteButton) {
                deleteButton.disabled = false;
            }
        }
    }

    // 更新行状态为 failed，并显示开始分析按钮
    function updateRowToFailed(fileId) {
        const row = document.querySelector(`.group[data-file-id="${fileId}"]`);
        if (row) {
            const actionCell = row.querySelector('.action-buttons');
            if (actionCell) {
                actionCell.innerHTML = `<button class="action-btn start-analysis-btn" data-file-id="${fileId}">开始分析</button>`;
                addEventListeners();  // 重新绑定事件监听器
            }

            // 重新启用删除按钮
            const deleteButton = row.querySelector('.delete-btn');
            if (deleteButton) {
                deleteButton.disabled = false;
            }
        }
    }

    // 获取状态文本函数
    function getStatusText(status) {
        switch(status) {
            case 'pending':
                return '待分析';
            case 'processing':
                return '处理中';
            case 'completed':
                return '已完成';
            case 'failed':
                return '分析失败';
            default:
                return status;
        }
    }

    // 添加按钮事件监听器函数
    function addEventListeners() {
        // 开始分析按钮
        const startAnalysisButtons = document.querySelectorAll('.start-analysis-btn');
        startAnalysisButtons.forEach(button => {
            button.removeEventListener('click', handleStartAnalysis); // 防止重复绑定
            button.addEventListener('click', handleStartAnalysis);
        });

        // 查看报告按钮
        const viewReportButtons = document.querySelectorAll('.view-report-btn');
        viewReportButtons.forEach(button => {
            button.removeEventListener('click', handleViewReport); // 防止重复绑定
            button.addEventListener('click', handleViewReport);
        });
    }

    // 处理开始分析按钮点击
    function handleStartAnalysis(event) {
        const fileId = this.getAttribute('data-file-id');
        const row = this.closest('.group');
        startAnalysis(fileId, row);
    }

    // 处理查看报告按钮点击
    function handleViewReport(event) {
        const fileId = this.getAttribute('data-file-id');
        viewReport(fileId);
    }

    // 添加长按事件监听器
    function addLongPressListeners() {
        const reports = document.querySelectorAll('.group');
        
        reports.forEach(report => {
            // 触摸事件（移动设备）
            report.addEventListener('touchstart', handleTouchStart);
            report.addEventListener('touchend', handleTouchEnd);
            report.addEventListener('touchmove', handleTouchMove);
            
            // 鼠标事件（桌面设备）
            report.addEventListener('mousedown', handleMouseDown);
            report.addEventListener('mouseup', handleMouseUp);
            report.addEventListener('mouseleave', handleMouseUp);
        });
    }

    // 处理触摸开始
    function handleTouchStart(e) {
        startLongPress(e.currentTarget);
    }

    // 处理触摸结束
    function handleTouchEnd() {
        clearLongPress();
    }

    // 处理触摸移动
    function handleTouchMove() {
        clearLongPress();
    }

    // 处理鼠标按下
    function handleMouseDown(e) {
        startLongPress(e.currentTarget);
    }

    // 处理鼠标松开
    function handleMouseUp() {
        clearLongPress();
    }

    // 开始长按计时
    function startLongPress(element) {
        pressTimer = setTimeout(() => {
            showDeleteConfirmation(element);
        }, longPressDuration);
    }

    // 清除长按计时
    function clearLongPress() {
        clearTimeout(pressTimer);
    }

    // 显示删除确认对话框
    function showDeleteConfirmation(element) {
        const fileId = element.dataset.fileId;
        if (confirm('确定要删除这份报告吗？此操作不可撤销。')) {
            deleteReport(fileId);
        }
    }

    // 删除报告
    async function deleteReport(fileId) {
        try {
            const token = localStorage.getItem('jwtToken');
            const response = await fetch(`/api/audio/delete_report/${fileId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const data = await response.json();
            
            if (data.code === 200) {
                alert('报告删除成功');
                // 重新获取报告列表
                fetchReportList();
            } else {
                alert(`删除失败：${data.msg}`);
            }
        } catch (error) {
            console.error('删除报告时出错:', error);
            alert('删除报告时发生错误，请稍后重试');
        }
    }

    // 添加CSS样式
    const style = document.createElement('style');
    style.textContent = `
        .group {
            user-select: none; /* 防止长按选中文本 */
            -webkit-user-select: none;
            -webkit-touch-callout: none;
        }
        
        .group.deleting {
            opacity: 0.5;
            transition: opacity 0.3s;
        }
    `;
    document.head.appendChild(style);

    // 检查登录状态并获取报告列表
    const token = localStorage.getItem('jwtToken');
    if (!token) {
        window.location.href = '/login';
    } else {
        fetchReportList();
    }

});