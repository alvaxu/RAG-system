/**
 * 测试智能显示逻辑的图表编号解析功能
 */

// 模拟LLM回答内容
const testAnswers = [
    "根据提供的文档内容，中芯国际的财务数据图表包括以下几类：\n\n1. **公司单季度营业收入及增速情况**  \n   - 图表编号：图1  \n   - 数据来源：Wind，中原证券研究所  \n   - 图表类型：信息图表  \n\n2. **公司单季度归母净利润及增速情况**  \n   - 图表编号：图2  \n   - 数据来源：Wind，中原证券研究所  \n   - 图表类型：信息图表",
    
    "根据提供的文档内容，2024年的营业收入数据图表对应的是：\n\n### **公司单季度营业收入及增速情况**\n- **图表编号**：图1  \n- **数据来源**：Wind，中原证券研究所  \n- **图表类型**：信息图表",
    
    "根据提供的文档内容，关于**净利润趋势图**的信息如下：\n\n### **公司单季度归母净利润及增速情况**\n- **图表编号**：图2  \n- **数据来源**：Wind，中原证券研究所  \n- **图表类型**：信息图表"
];

// 模拟图片源数据
const testImageSources = [
    {
        metadata: {
            image_id: "e27d2aad5f5f952e58f7df5272c9c9a4567b605a52dbdff8b678e08699541398",
            img_caption: ["图1：公司单季度营业收入及增速情况"],
            img_footnote: ["资料来源：Wind，中原证券研究所"]
        }
    },
    {
        metadata: {
            image_id: "dea4ce191c09e7fc70c99674cf00dcb13c797db859a58d3a9ec9663348b01b20",
            img_caption: ["图2：公司单季度归母净利润及增速情况"],
            img_footnote: ["资料来源：Wind，中原证券研究所"]
        }
    },
    {
        metadata: {
            image_id: "60a552470e2a2e10a7f98a88d9bd8472e62f9e198adab413b9f98bc37931aef7",
            img_caption: ["图3：公司单季度毛利率及净利率情况"],
            img_footnote: ["资料来源：Wind，中原证券研究所"]
        }
    }
];

/**
 * 从LLM回答中解析图表编号引用
 */
function parseChartNumbersFromAnswer(answer) {
    const chartNumbers = new Set();
    const chartPatterns = [
        /图(\d+)/g,
        /图表(\d+)/g,
        /图表编号[：:]\s*图(\d+)/g,
        /图表编号[：:]\s*(\d+)/g
    ];
    
    chartPatterns.forEach(pattern => {
        let match;
        while ((match = pattern.exec(answer)) !== null) {
            chartNumbers.add(match[1]);
        }
    });
    
    return chartNumbers;
}

/**
 * 根据LLM回答智能过滤图片
 */
function filterImagesByLLMAnswer(answer, imageSources) {
    const llmChartNumbers = parseChartNumbersFromAnswer(answer);
    
    console.log(`解析到的图表编号: ${Array.from(llmChartNumbers)}`);
    
    return imageSources.filter(source => {
        const metadata = source.metadata;
        const captionText = (metadata.img_caption || []).join(' ');
        
        // 检查图表编号是否在LLM回答中被提到
        for (const chartNumber of llmChartNumbers) {
            if (captionText.includes(`图${chartNumber}`) || captionText.includes(`图表${chartNumber}`)) {
                console.log(`匹配成功: 图表编号${chartNumber} -> ${captionText}`);
                return true;
            }
        }
        
        return false;
    });
}

// 测试每个回答
console.log("=== 测试智能显示逻辑 ===\n");

testAnswers.forEach((answer, index) => {
    console.log(`测试 ${index + 1}:`);
    console.log(`LLM回答: ${answer.substring(0, 100)}...`);
    
    const filteredImages = filterImagesByLLMAnswer(answer, testImageSources);
    
    console.log(`过滤结果: ${filteredImages.length} 张图片`);
    filteredImages.forEach((img, imgIndex) => {
        const caption = img.metadata.img_caption.join(' ');
        console.log(`  ${imgIndex + 1}. ${caption}`);
    });
    console.log("\n");
}); 