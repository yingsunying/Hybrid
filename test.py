import os
import json
from aip import AipOcr
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_baidu_ocr_credentials():
    """测试百度OCR API凭据是否有效"""
    
    # 获取环境变量
    app_id = os.getenv("BAIDU_OCR_APP_ID")
    api_key = os.getenv("BAIDU_OCR_API_KEY")
    secret_key = os.getenv("BAIDU_OCR_SECRET_KEY")
    
    print("=== 百度OCR凭据测试 ===")
    print(f"APP_ID: {app_id[:4]}...{app_id[-4:] if app_id else 'None'}")
    print(f"API_KEY: {api_key[:4]}...{api_key[-4:] if api_key else 'None'}")
    print(f"SECRET_KEY: {secret_key[:4]}...{secret_key[-4:] if secret_key else 'None'}")
    
    # 检查是否所有凭据都存在
    if not all([app_id, api_key, secret_key]):
        print("❌ 错误：缺少必要的API凭据")
        return False
    
    try:
        # 初始化客户端
        client = AipOcr(app_id, api_key, secret_key)
        print("✅ AipOcr客户端初始化成功")
        
        # 创建一个简单的测试图片（纯色图片）
        import PIL.Image as Image
        import io
        
        # 创建一个包含文字的简单图片用于测试
        img = Image.new('RGB', (200, 100), color='white')
        
        # 将图片转换为字节数据
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        print("📸 使用测试图片调用API...")
        
        # 调用基础OCR接口（免费版本）
        result = client.basicGeneral(img_byte_arr)
        
        print("=== API响应结果 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 检查响应结果
        if 'error_code' in result:
            print(f"❌ API调用失败")
            print(f"错误代码: {result['error_code']}")
            print(f"错误信息: {result.get('error_msg', '未知错误')}")
            
            # 提供错误代码的解释
            error_explanations = {
                1: "未知错误",
                2: "服务暂不可用",
                3: "调用的API不存在",
                4: "集群超负荷",
                6: "无权限访问该用户数据",
                14: "IAM鉴权失败",
                15: "应用不存在，请核对app_id是否正确",
                17: "每天流量超限额",
                18: "QPS超限额",
                19: "请求总量超限额",
                100: "无效参数",
                216015: "模块关闭",
                282000: "服务端内部错误",
                282003: "请求参数缺失",
                282005: "处理失败",
                282006: "批量任务处理部分成功",
                282007: "批量任务全部处理失败",
                282114: "接口能力未开通或已关闭"
            }
            
            if result['error_code'] in error_explanations:
                print(f"解释: {error_explanations[result['error_code']]}")
            
            return False
        else:
            print("✅ API调用成功")
            if 'words_result_num' in result:
                print(f"识别到 {result['words_result_num']} 行文字")
            return True
            
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        return False

def check_account_quota():
    """检查账户配额使用情况"""
    print("\n=== 账户配额建议检查项 ===")
    print("请登录百度智能云控制台检查以下项目：")
    print("1. 文字识别 -> 概览 -> 调用量统计")
    print("2. 账户中心 -> 资源包管理")
    print("3. 文字识别 -> 应用列表 -> 查看应用状态")
    print("4. 账户中心 -> 安全设置 -> IP白名单")

if __name__ == "__main__":
    success = test_baidu_ocr_credentials()
    
    if not success:
        check_account_quota()
        print("\n=== 解决建议 ===")
        print("1. 检查百度智能云控制台中的服务状态")
        print("2. 确认文字识别服务已正确开通")
        print("3. 检查API凭据是否正确")
        print("4. 确认账户余额和配额充足")
        print("5. 检查IP是否在白名单中（如果设置了IP限制）")
    else:
        print("\n✅ API测试通过，凭据配置正确")