// 使用原生fetch API类型

// 创建API配置
const API_CONFIG = {
  // 默认API地址，用户可以在这里修改
  BASE_URL: 'https://59a7efd42ee84d2db8811534a003270b--5001.ap-shanghai2.cloudstudio.club',
  // 请求超时时间
  TIMEOUT: 60000,
  // 默认请求头
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json'
  }
};

/**
 * API响应类型
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

/**
 * 统一API请求函数
 * @param url 请求路径
 * @param config fetch请求配置
 * @returns Promise<ApiResponse>
 */
export const apiRequest = async <T = any>(
  url: string,
  config: RequestInit = {}
): Promise<ApiResponse<T>> => {
  try {
    // 构建完整URL
    const fullUrl = `${API_CONFIG.BASE_URL}${url}`;
    
    // 合并请求配置
    const requestConfig: RequestInit = {
      ...config,
      headers: {
        ...API_CONFIG.DEFAULT_HEADERS,
        ...(config.headers || {})
      }
    };
    
    // 处理请求体
    let requestBody: BodyInit | null = null;
    const contentType = requestConfig.headers && (requestConfig.headers as Record<string, string>)['Content-Type'];
    
    if (requestConfig.body && contentType === 'application/json' && typeof requestConfig.body === 'object') {
      requestBody = JSON.stringify(requestConfig.body);
    } else if (requestConfig.body) {
      requestBody = requestConfig.body;
    }
    
    // 发送请求
    const response = await fetch(fullUrl, {
      method: requestConfig.method || 'GET',
      headers: requestConfig.headers,
      body: requestBody,
      signal: requestConfig.signal,
      credentials: requestConfig.credentials || 'same-origin'
    });
    
    // 解析响应数据
    let responseData: any;
    try {
      responseData = await response.json();
    } catch (error) {
      responseData = null;
    }
    
    // 处理响应
    if (response.ok) {
      return {
        success: true,
        data: responseData as T
      };
    } else {
      return {
        success: false,
        error: responseData?.error || responseData?.message || `请求失败: ${response.status}`,
        message: responseData?.message
      };
    }
  } catch (error) {
    console.error('API请求错误:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : '网络请求失败',
      message: '网络请求失败，请检查您的网络连接'
    };
  }
};

/**
 * GET请求
 * @param url 请求路径
 * @param config fetch请求配置
 * @returns Promise<ApiResponse>
 */
export const get = <T = any>(url: string, config: Omit<RequestInit, 'method'> = {}): Promise<ApiResponse<T>> => {
  return apiRequest<T>(url, { ...config, method: 'GET' });
};

/**
 * POST请求
 * @param url 请求路径
 * @param data 请求数据
 * @param config fetch请求配置
 * @returns Promise<ApiResponse>
 */
export const post = <T = any>(
  url: string,
  data?: any,
  config: Omit<RequestInit, 'method' | 'body'> = {}): Promise<ApiResponse<T>> => {
  return apiRequest<T>(url, { ...config, method: 'POST', body: data });
};

/**
 * PUT请求
 * @param url 请求路径
 * @param data 请求数据
 * @param config fetch请求配置
 * @returns Promise<ApiResponse>
 */
export const put = <T = any>(
  url: string,
  data?: any,
  config: Omit<RequestInit, 'method' | 'body'> = {}): Promise<ApiResponse<T>> => {
  return apiRequest<T>(url, { ...config, method: 'PUT', body: data });
};

/**
 * DELETE请求
 * @param url 请求路径
 * @param config fetch请求配置
 * @returns Promise<ApiResponse>
 */
export const del = <T = any>(url: string, config: Omit<RequestInit, 'method'> = {}): Promise<ApiResponse<T>> => {
  return apiRequest<T>(url, { ...config, method: 'DELETE' });
};

/**
 * 表单数据请求 (multipart/form-data)
 * @param url 请求路径
 * @param formData FormData对象
 * @param config fetch请求配置
 * @returns Promise<ApiResponse>
 */
export const postForm = <T = any>(
  url: string,
  formData: FormData,
  config: Omit<RequestInit, 'method' | 'body' | 'headers'> = {}): Promise<ApiResponse<T>> => {
  return apiRequest<T>(url, {
    ...config,
    method: 'POST',
    body: formData,
    // 不要手动设置Content-Type，浏览器会自动设置正确的Content-Type（包括boundary）
    headers: {}
  });
};

/**
 * 更新API基础地址
 * @param baseUrl 新的API基础地址
 */
export const setApiBaseUrl = (baseUrl: string): void => {
  API_CONFIG.BASE_URL = baseUrl;
};

/**
 * 获取当前API基础地址
 * @returns 当前API基础地址
 */
export const getApiBaseUrl = (): string => {
  return API_CONFIG.BASE_URL;
};
