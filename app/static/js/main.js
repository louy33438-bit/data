// 全局变量
let searchResults = [];
let currentRawData = []; // 用于存储原始数据仓库中的数据
let currentPage = 1;
const itemsPerPage = 10;

// 页面加载完成后初始化
$(document).ready(function() {
    // 搜索功能
    $('#search-form').on('submit', function(e) {
        e.preventDefault();
        performSearch();
    });
    
    // 全选/取消全选按钮点击事件
    $('#select-all-btn').on('click', function() {
        $('.result-checkbox').prop('checked', true);
        // 更新全选状态显示
        $(this).text('已全选');
    });
    
    // 取消全选按钮点击事件
    $('#deselect-all-btn').on('click', function() {
        $('.result-checkbox').prop('checked', false);
        // 更新全选按钮文本
        $('#select-all-btn').text('全选');
    });
    
    // 单个选择框改变时更新全选状态
    $('.results-list').on('change', '.result-checkbox', function() {
        const allChecked = $('.result-checkbox').length === $('.result-checkbox:checked').length;
        $('#select-all-btn').text(allChecked ? '已全选' : '全选');
    });
    
    // 批量保存按钮点击事件
    $('#save-selected-btn').on('click', saveSelectedResults);
    
    // 数据仓库筛选表单提交
    $('#filter-form').on('submit', function(e) {
        e.preventDefault();
        filterData();
    });
    
    // 清空筛选条件
    $('#reset-filter').on('click', clearFilter);
    
    // 页面加载完成后自动加载初始数据
    filterData();
    
    // 分页按钮事件委托
    $(document).on('click', '.pagination-btn', function() {
        if ($(this).hasClass('active') || $(this).prop('disabled')) return;
        
        const pageText = $(this).text();
        if (pageText === '上一页') {
            currentPage--;
        } else if (pageText === '下一页') {
            currentPage++;
        } else {
            currentPage = parseInt(pageText);
        }
        
        renderPagination();
    });
});

// 执行搜索
function performSearch() {
    const keyword = $('#search-keyword').val().trim();
    if (!keyword) {
        showAlert('请输入搜索关键词', 'error');
        return;
    }
    
    console.log('开始搜索:', keyword);
    
    // 显示搜索按钮加载状态
    const searchBtn = $('#search-btn');
    const originalBtnHtml = searchBtn.html();
    searchBtn.html('<i class="search-icon">⏳</i><span>搜索中...</span>').prop('disabled', true);
    
    // 显示加载状态
    showLoading();
    
    // 确保结果区域可见
    $('#results-section').show();
    
    // 重置搜索结果数组
    searchResults = [];
    currentPage = 1;
    
    // 发送搜索请求
    $.ajax({
        url: '/search',
        type: 'POST',
        data: { keyword: keyword },
        timeout: 30000, // 设置30秒超时
        success: function(response) {
            console.log('搜索响应:', response);
            
            // 根据后端返回的格式调整判断条件
            if (response.status === 'success') {
                searchResults = response.results; // 存储所有搜索结果
                renderResults(searchResults);
                renderPagination();
                
                // 如果是模拟结果，显示提示
                if (response.is_mock) {
                    showAlert('当前显示的是模拟结果，实际搜索可能需要调整', 'warning');
                    console.warn('显示的是模拟搜索结果');
                } else {
                    showAlert(`搜索完成，共找到 ${response.results.length} 条结果`, 'success');
                }
            } else {
                const errorMessage = response.message || '搜索失败';
                showAlert(errorMessage, 'error');
                renderEmptyResults();
                console.error('搜索错误:', errorMessage);
            }
        },
        error: function(xhr, status, error) {
            let errorMessage = '网络错误，请稍后重试';
            
            if (status === 'timeout') {
                errorMessage = '搜索超时，请尝试更简短的关键词';
            } else if (xhr.status === 404) {
                errorMessage = '搜索接口不存在';
            } else if (xhr.status === 500) {
                errorMessage = '服务器内部错误，请稍后重试';
            } else {
                errorMessage = '网络错误，请检查您的连接';
            }
            
            console.error('搜索请求错误:', status, error, xhr.status);
            
            // 尝试从错误响应中获取更详细的错误信息
            try {
                const errorResponse = JSON.parse(xhr.responseText);
                if (errorResponse.message) {
                    errorMessage = errorResponse.message;
                }
            } catch (e) {
                console.log('无法解析错误响应:', e);
            }
            
            // 显示错误信息
            showAlert(errorMessage, 'error');
            
            // 添加模拟结果以保持UI一致性
            const mockResults = [{
                'title': `关于"${keyword}"的示例结果`,
                'url': '#',
                'summary': '这是一个模拟的搜索结果。实际搜索功能可能需要修复或调整。',
                'source': '系统测试'
            }];
            
            searchResults = mockResults;
            renderResults(searchResults);
            renderPagination();
        },
        complete: function() {
            // 恢复搜索按钮原始状态
            searchBtn.html(originalBtnHtml).prop('disabled', false);
            hideLoading();
        }
    });
}

// 获取用户在页面上选中的文本
function getUserSelectedText() {
    let selectedText = '';
    if (window.getSelection) {
        selectedText = window.getSelection().toString();
    } else if (document.selection && document.selection.type !== 'Control') {
        selectedText = document.selection.createRange().text;
    }
    return selectedText.trim();
}

// 保存选中的结果
function saveSelectedResults() {
    // 检测当前页面类型
    const isDataWarehousePage = window.location.pathname.includes('/data_warehouse');
    
    // 获取用户选中文本
    const selectedText = getUserSelectedText();
    
    // 根据页面类型选择对应的复选框
    const checkboxClass = isDataWarehousePage ? '.data-checkbox:checked' : '.result-checkbox:checked';
    const selectedItems = $(checkboxClass);
    
    // 检查是否有选中项或选中文本
    if (selectedItems.length === 0 && selectedText === '') {
        showAlert('请选择数据项或选中文本', 'error');
        return;
    }
    
    console.log('开始保存，选中项数量:', selectedItems.length, '页面类型:', isDataWarehousePage ? '数据仓库' : '搜索结果');
    
    // 如果是数据仓库页面，不应该再次保存数据到原始表
    if (isDataWarehousePage) {
        showAlert('数据仓库中的数据已保存，无需重复保存', 'info');
        return;
    }
    
    let selectedData = [];
    
    // 处理选中文本
    if (selectedText !== '') {
        // 创建一个新的数据项
        const textItem = {
            title: selectedText.substring(0, 50) + (selectedText.length > 50 ? '...' : ''),
            content: selectedText,
            source: '用户手动选择',
            keyword: $('#search-keyword').val().trim() || '未知',
            url: window.location.href
        };
        selectedData.push(textItem);
        console.log('添加选中文本数据项:', textItem.title);
    }
    
    // 处理选中的复选框数据
    selectedItems.each(function() {
        const index = $(this).data('index');
        let item;
        
        // 从搜索结果中获取数据
        if (index !== undefined && searchResults[index] !== undefined) {
            item = { ...searchResults[index] };
        }
        
        if (item) {
            // 标准化来源名称
            if (item.source) {
                if (item.source.includes('百度')) item.source = '百度';
                if (item.source.includes('B站') || item.source.includes('Bilibili')) item.source = 'Bilibili';
            }
            
            // 添加必要的字段
            if (!item.keyword) {
                item.keyword = $('#search-keyword').val().trim() || '未知';
            }
            
            selectedData.push(item);
            console.log('添加数据项:', item.title, '来源:', item.source);
        } else {
            showAlert('获取选中数据失败，请重试', 'error');
            return false; // 退出each循环
        }
    });
    
    // 确保每个数据项都有必要的字段
    selectedData = selectedData.map(item => ({
        title: item.title || '无标题',
        url: item.url || '',
        source: item.source || '未知',
        summary: item.summary || '',
        content: item.content || '',
        // 确保不包含undefined或null值
        ...Object.fromEntries(Object.entries(item).filter(([_, v]) => v !== undefined && v !== null))
    }));
    console.log('数据项规范化后:', selectedData.length, '条数据');
    
    // 显示加载状态
    showLoading();
    
    // 发送保存请求
    const keyword = $('#search-keyword').val().trim() || '未知';
    console.log('发送保存请求，关键词:', keyword);
    
    // 构建最终发送的数据
    const saveData = {
        results: selectedData,
        keyword: keyword
    };
    console.log('最终发送的数据结构:', JSON.stringify(saveData, null, 2));
    
    $.ajax({
        url: '/save_data',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(saveData),
        // 添加超时设置
        timeout: 10000,
        success: function(response) {
            console.log('保存响应详情:', JSON.stringify(response));
            // 根据后端返回的格式调整判断条件
            if (response) {
                if (response.status === 'success') {
                    console.log('保存成功，准备跳转...');
                    showAlert('数据保存成功，正在跳转到数据仓库...', 'success');
                    // 清除已保存的数据选中状态
                    $('.result-checkbox:checked').prop('checked', false);
                    $('#select-all-btn').text('全选');
                    
                    // 延迟1.5秒后跳转到数据仓库界面，让用户有时间看到成功提示
                    setTimeout(function() {
                        console.log('执行跳转至数据仓库页面');
                        window.location.href = '/data_warehouse';
                    }, 1500);
                } else if (response.status === 'info') {
                    console.log('保存信息，响应:', response);
                    showAlert(response.message ? response.message : '操作已完成', 'info');
                } else {
                    console.error('保存失败，响应:', response);
                    showAlert(response && response.message ? response.message : '保存失败，未知错误', 'error');
                }
            } else {
                console.error('保存失败，响应为空');
                showAlert('保存失败，服务器没有返回响应', 'error');
            }
        },
        error: function(xhr) {
            console.log('保存请求错误，状态码:', xhr.status);
            // 尝试从错误响应中获取更详细的错误信息
            let errorMessage = '网络错误，请稍后重试';
            try {
                const errorResponse = JSON.parse(xhr.responseText);
                if (errorResponse && errorResponse.message) {
                    errorMessage = errorResponse.message;
                }
            } catch (e) {
                console.log('无法解析错误响应:', e);
                console.log('原始响应:', xhr.responseText);
                errorMessage = `保存失败，状态码: ${xhr.status}`;
            }
            showAlert(errorMessage, 'error');
        },
        complete: function() {
            hideLoading();
        }
    });
}

// 筛选数据 - 确保使用正确的/get_raw_data接口
function filterData() {
    const date = $('#date-filter').val();
    const keyword = $('#search-keyword').val().trim();
    
    // 显示加载状态
    showLoading();
    
    // 发送筛选请求 - 确保使用正确的/get_raw_data接口（GET方法）
    $.ajax({
        url: '/get_raw_data',
        type: 'GET',
        data: { date: date || '', keyword: keyword },
        success: function(response) {
            // 修复数据渲染逻辑，确保正确处理响应格式
            if (response && response.data && Array.isArray(response.data)) {
                renderDataList(response.data);
                updateDataStats(response.data.length);
            } else {
                showAlert(response && response.message ? response.message : '筛选失败', 'error');
                renderEmptyData();
            }
        },
        error: function(xhr) {
            // 尝试从错误响应中获取更详细的错误信息
            let errorMessage = '网络错误，请稍后重试';
            try {
                const errorResponse = JSON.parse(xhr.responseText);
                if (errorResponse && errorResponse.message) {
                    errorMessage = errorResponse.message;
                }
            } catch (e) {
                console.log('无法解析错误响应:', e);
            }
            showAlert(errorMessage, 'error');
            renderEmptyData();
        },
        complete: function() {
            hideLoading();
        }
    });
}

// 清空筛选条件
function clearFilter() {
    $('#date-filter').val('');
    $('#search-keyword').val('');
    filterData();
}

// 渲染搜索结果
function renderResults(results) {
    const resultsList = $('.results-list');
    resultsList.empty();
    
    if (results.length === 0) {
        renderEmptyResults();
        return;
    }
    
    // 获取当前页的数据
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const currentPageResults = results.slice(startIndex, endIndex);
    
    currentPageResults.forEach((item, index) => {
        const actualIndex = startIndex + index; // 使用实际的全局索引
        const source = item.source || '未知来源';
        // 根据来源添加不同的样式类
        let sourceClass = 'source-tag';
        let sourceLabel = source;
        if (source.includes('百度')) {
            sourceClass = 'source-tag baidu-source';
            sourceLabel = '百度';
        } else if (source.includes('Bilibili')) {
            sourceClass = 'source-tag bilibili-source';
            sourceLabel = 'B站';
        }
        
        // 处理摘要中的换行符
        const formattedSummary = (item.summary || '无摘要').replace(/\n/g, '<br>');
        
        // 确保标题可点击，如果有URL的话
        let titleHtml = item.url ? 
            `<a href="${escapeHtml(item.url)}" target="_blank" class="result-title-link">${escapeHtml(item.title || '无标题')}</a>` : 
            escapeHtml(item.title || '无标题');
        
        // URL显示为可点击链接
        let urlHtml = item.url ? 
            `<a href="${escapeHtml(item.url)}" target="_blank" class="result-url-link">${escapeHtml(item.url)}</a>` : 
            '';
        
        const resultItem = $('<div class="result-item">').html(`
            <div class="result-header">
                <input type="checkbox" class="result-checkbox" data-index="${actualIndex}">
                <div class="result-content">
                    <div class="result-title">
                        ${titleHtml}
                        <span class="${sourceClass}">${escapeHtml(sourceLabel)}</span>
                    </div>
                    <div class="result-url">${urlHtml}</div>
                    <div class="result-summary">${formattedSummary}</div>
                    <div class="result-meta">
                        <span class="data-source">来源: ${escapeHtml(sourceLabel)}</span>
                    </div>
                </div>
            </div>
        `);
        resultsList.append(resultItem);
    });
}

// 渲染数据仓库列表
function renderDataList(data) {
    const dataList = $('.data-list');
    dataList.empty();
    
    if (data.length === 0) {
        renderEmptyData();
        return;
    }
    
    // 存储当前显示的原始数据
    currentRawData = data;
    
    data.forEach((item, index) => {
        // 确保标题可点击，如果有URL的话
        let titleHtml = item.url ? 
            `<h4><a href="${escapeHtml(item.url)}" target="_blank" class="data-title-link">${escapeHtml(item.title || '无标题')}</a></h4>` : 
            `<h4>${escapeHtml(item.title || '无标题')}</h4>`;
            
        // 标准化来源显示
        let sourceDisplay = item.source;
        if (sourceDisplay) {
            if (sourceDisplay.includes('百度')) sourceDisplay = '百度';
            if (sourceDisplay.includes('B站') || sourceDisplay.includes('Bilibili')) sourceDisplay = 'B站';
        } else {
            sourceDisplay = '未知';
        }
            
        const dataItem = $('<div class="data-item">').html(`
            <div class="data-item-header">
                <input type="checkbox" class="data-checkbox" data-index="${index}">
                ${titleHtml}
            </div>
            <div class="data-item-meta">
                <span>关键词：${escapeHtml(item.keyword || '未知')}</span>
                <span>日期：${formatDate(item.created_at)}</span>
                <span>来源：${escapeHtml(sourceDisplay)}</span>
            </div>
            <div class="data-item-summary">${escapeHtml(item.content || '无内容')}</div>
            <div class="data-item-actions">
                <button class="btn btn-secondary view-details">查看详情</button>
                <button class="btn btn-primary generate-report">生成报告</button>
            </div>
        `);
        dataList.append(dataItem);
    });
}

// 渲染分页
function renderPagination() {
    const pagination = $('.pagination');
    pagination.empty();
    
    const totalPages = Math.ceil(searchResults.length / itemsPerPage);
    if (totalPages <= 1) return;
    
    // 上一页按钮
    const prevBtn = $('<button class="pagination-btn">').text('上一页')
        .prop('disabled', currentPage === 1);
    pagination.append(prevBtn);
    
    // 页码按钮
    const pageRange = 3;
    let startPage = Math.max(1, currentPage - pageRange);
    let endPage = Math.min(totalPages, startPage + pageRange * 2);
    
    if (endPage - startPage < pageRange * 2) {
        startPage = Math.max(1, endPage - pageRange * 2);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = $('<button class="pagination-btn">').text(i)
            .toggleClass('active', i === currentPage);
        pagination.append(pageBtn);
    }
    
    // 下一页按钮
    const nextBtn = $('<button class="pagination-btn">').text('下一页')
        .prop('disabled', currentPage === totalPages);
    pagination.append(nextBtn);
}

// 更新数据统计
function updateDataStats(count) {
    $('.data-stats').text(`共 ${count} 条数据`);
}

// 显示加载状态
function showLoading() {
    $('.results-list, .data-list').html(`
        <div class="loading">
            <div class="loading-spinner"></div>
            <p>正在处理...</p>
        </div>
    `);
}

// 隐藏加载状态
function hideLoading() {
    // 加载状态会在渲染结果时自动移除
}

// 渲染空结果
function renderEmptyResults() {
    $('.results-list').html(`
        <div class="results-empty">
            <p>暂无搜索结果</p>
        </div>
    `);
    $('.pagination').empty();
}

// 渲染空数据
function renderEmptyData() {
    $('.data-list').html(`
        <div class="data-empty">
            <p>暂无数据</p>
        </div>
    `);
}

// 显示提示信息
function showAlert(message, type = 'error') {
    let alertClass;
    switch(type) {
        case 'success':
            alertClass = 'alert-success';
            break;
        case 'info':
            alertClass = 'alert-info';
            break;
        default:
            alertClass = 'alert-error';
    }
    const alert = $('<div class="alert">').addClass(alertClass).text(message);
    
    // 如果是登录页面，添加到登录表单之前
    if ($('.login-form').length > 0) {
        $('.login-form').before(alert);
    } else {
        $('.content').prepend(alert);
    }
    
    // 3秒后自动移除
    setTimeout(() => {
        alert.fadeOut('slow', function() {
            $(this).remove();
        });
    }, 3000);
}

// HTML转义
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// 日期格式化
function formatDate(dateString) {
    if (!dateString) return '未知';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}