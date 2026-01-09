// 使用原生fetch API类型

// 创建API配置
const API_CONFIG = {
  // 默认API地址，用户可以在这里修改
  BASE_URL: '/api',
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
    
    // 合并请求配置并添加认证token
    const requestConfig: RequestInit = {
      ...config,
      headers: {
        ...(config.headers ? {} : API_CONFIG.DEFAULT_HEADERS),
        ...(config.headers || {})
      }
    };
    
    // 从localStorage获取认证token
    const token = localStorage.getItem('authToken');
    if (token) {
      // 添加Authorization头
      (requestConfig.headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }
    
    // 处理请求体
    let requestBody: BodyInit | null = null;
    const contentType = requestConfig.headers && (requestConfig.headers as Record<string, string>)['Content-Type'];
    
    if (requestConfig.body && contentType === 'application/json' && typeof requestConfig.body === 'object' && !(requestConfig.body instanceof FormData)) {
      requestBody = JSON.stringify(requestConfig.body);
    } else if (requestConfig.body) {
      requestBody = requestConfig.body;
    }
    
    // 发送请求
    const fetchConfig: RequestInit = {
      method: requestConfig.method || 'GET',
      signal: requestConfig.signal,
      credentials: requestConfig.credentials || 'same-origin'
    };
    
    // 只有当 headers 不为空时才设置 headers 参数
    if (Object.keys(requestConfig.headers || {}).length > 0) {
      fetchConfig.headers = requestConfig.headers;
    }
    
    // 设置请求体
    fetchConfig.body = requestBody;
    
    const response = await fetch(fullUrl, fetchConfig);
    
    // 解析响应数据
    let responseData: any;
    try {
      responseData = await response.json();
    } catch (error) {
      responseData = null;
    }
    
    // 处理响应
    if (responseData) {
      // 根据后端返回的code判断请求是否成功
      // 后端通常返回code为200表示成功
      const isSuccess = responseData.code === 200;
      return {
        success: isSuccess,
        data: responseData.data as T,
        error: !isSuccess ? (responseData.msg || `请求失败: ${response.status}`) : undefined,
        message: responseData.msg
      };
    } else {
      return {
        success: false,
        error: `请求失败: ${response.status}`,
        message: `请求失败: ${response.status}`
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
  const token = localStorage.getItem('authToken');
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return apiRequest<T>(url, {
    ...config,
    method: 'POST',
    body: formData,
    // 不要手动设置Content-Type，浏览器会自动设置正确的Content-Type（包括boundary）
    headers
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

/**
 * LoRA配置类型
 */
export interface LoraConfig {
  id: number;
  name: string;
  path: string;
  strength: number | null;
}

/**
 * LoRA配置响应类型
 */
export interface LoraConfigResponse {
  wan_2_1_t2v: LoraConfig[]; // 文生视频
  wan_2_2_i2v: LoraConfig[]; // 图生视频
  qwen_image_edit: LoraConfig[]; // 图生图
  z_image: LoraConfig[]; // 文生图
}

/**
 * 获取LoRA配置
 * @returns Promise<ApiResponse<LoraConfigResponse>>
 */
export const getLoraConfig = async (): Promise<ApiResponse<LoraConfigResponse>> => {
  return get<LoraConfigResponse>('/lora/config');
};
