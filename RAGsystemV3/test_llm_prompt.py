#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LLM是否能理解包含历史记忆的prompt
"""

import requests
import json

def test_llm_with_history():
    """测试LLM是否能理解包含历史记忆的prompt"""
    print("🧠 测试LLM理解能力")
    print("=" * 60)
    
    # 构建包含历史记忆的prompt
    history_memory = """用户询问: 中芯国际是什么公司？
系统回答: 中芯国际（SMIC，全称为"上海中芯国际集成电路制造有限公司"）是一家世界领先的集成电路晶圆代工企业，总部位于中国上海。公司主要为全球客户提供8英寸和12英寸晶圆的代工与技术服务，覆盖从设计到制造的完整半导体产业链环节。

作为国内IC制造领域的领军企业，中芯国际不仅具备强大的技术研发能力，还构建了高度全球化的业务布局：其生产、制造与服务体系遍布全球，在美国、欧洲、日本、中国台湾等地设有多个营销办事处，实现服务全球化。

此外，中芯国际与世界级IC设计公司、标准单元库提供商、EDA工具厂商、封装测试企业以及设备和材料供应商建立了紧密合作关系，形成了完整的上下游生态链，持续推动工艺技术迭代升级，并在全球半导体行业中发挥重要作用。"""

    # 构建完整的prompt
    prompt = f"""你是一个专业的AI助手，能够基于提供的上下文信息生成准确、相关、完整的答案。

基于以下上下文信息回答问题：

上下文：
文本信息：
{history_memory}

问题：
它的主要业务是什么？

请提供准确、详细的答案："""

    print("📝 测试Prompt:")
    print("-" * 40)
    print(prompt)
    print("-" * 40)
    
    # 使用RAG查询API测试
    try:
        response = requests.post("http://localhost:8000/api/v3/rag/query", json={
            "query": "它的主要业务是什么？",
            "query_type": "text",
            "user_id": "test_user",
            "session_id": "test_session"
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            print(f"\n🤖 LLM回答:")
            print(answer)
            
            # 检查回答是否理解"它"指中芯国际
            if '中芯国际' in answer or 'SMIC' in answer:
                print("\n✅ LLM正确理解了'它'指中芯国际")
            else:
                print("\n❌ LLM没有理解'它'指中芯国际")
        else:
            print(f"❌ LLM调用失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_llm_with_history()
