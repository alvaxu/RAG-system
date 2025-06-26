[toc]



# 自定义MCP 运行txt_counter.py



```powershell
PS D:\cursorprj\lecture11\CASE-MCP Demo-1> mcp dev txt_counter_practice.py  
Starting MCP inspector...
⚙️ Proxy server listening on port 6277
🔍 MCP Inspector is up and running at http://127.0.0.1:6274 🚀


```

![image-20250510092716477](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20250510092716477.png)

![image-20250510092702358](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20250510092702358.png)

![image-20250510092807803](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20250510092807803.png)



![image-20250510093038456](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20250510093038456.png)

![image-20250510093059510](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20250510093059510.png)

![image-20250510093143420](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20250510093143420.png)



#将自定义的MCP功能加到 assistant_bot practice2.py中

## 方法一 ：失败



你可以这样将自定义的txt_counter_practice.py（本地MCP服务，端口6274）集成到 assistant_bot practice2.py 的MCP配置中：

---

### 步骤说明

1. **在tools的mcpServers中增加txt-counter-practice配置**  
2. **指定type为sse，url为 http://127.0.0.1:6274/**

---

### 修改建议（assistant_bot practice2.py）

找到如下片段（大约在50行左右）：

```python
tools = [{
    "mcpServers": {
        "amap-maps": {
            "command": "npx",
            "args": [
                "-y",
                "@amap/amap-maps-mcp-server"
            ],
            "env": {
                "AMAP_MAPS_API_KEY": "96e6841038817fab25821697f44d15c8"
            }
        },
        "fetch": {
            "type": "sse",
            "url": "https://mcp.api-inference.modelscope.cn/sse/729c49665d834c"
       },
        "bing-cn-mcp-server": {
            "type": "sse",
            "url": "https://mcp.api-inference.modelscope.cn/sse/2aba790abd024b"
        }
    }
}]
```

**在`"mcpServers"`字典中添加如下内容：**

```python
"txt-counter-practice": {
    "type": "sse",
    "url": "http://127.0.0.1:6274/"
}
```

---

### 修改后完整片段示例

```python
tools = [{
    "mcpServers": {
        "amap-maps": {
            "command": "npx",
            "args": [
                "-y",
                "@amap/amap-maps-mcp-server"
            ],
            "env": {
                "AMAP_MAPS_API_KEY": "96e6841038817fab25821697f44d15c8"
            }
        },
        "fetch": {
            "type": "sse",
            "url": "https://mcp.api-inference.modelscope.cn/sse/729c49665d834c"
        },
        "bing-cn-mcp-server": {
            "type": "sse",
            "url": "https://mcp.api-inference.modelscope.cn/sse/2aba790abd024b"
        },
        "txt-counter-practice": {
            "type": "sse",
            "url": "http://127.0.0.1:6274/"
        }
    }
}]
```

---

这样你就可以在 Assistant 里通过 `txt-counter-practice` 这个MCP服务，调用你自定义的txt统计相关API了！

如需进一步自定义工具名或参数，请告知你的具体需求。





## 方法二

发现我们不能简单地将自定义的txt-counter-practice的MCP服务器加进去，还得调整一下配置，以适合MCPserver的配置情况

你的分析完全正确！  
你自定义的 `txt_counter_practice.py` 是用 `mcp dev` 启动的，实际上它是一个**MCP本地开发服务器**，而 Assistant 的 `mcpServers` 配置里 `"type": "sse"` 适用于**远程SSE协议**的MCP服务（如官方云端MCP），而本地开发MCP服务需要用 `"type": "http"` 并指定 `port`。

---

### 正确的本地MCP配置方法

请将 `txt-counter-practice` 的配置改为如下格式：

```python
"txt-counter-practice": {
    "command": "python",
    "args": ["txt_counter_practice.py"],
    "port": 6274
}
```

这样 Assistant 会自动在本地以 HTTP 方式调用 MCP 工具，而不是用 SSE 协议。

---

### 完整配置片段示例

```python
tools = [{
    "mcpServers": {
        "amap-maps": {
            "command": "npx",
            "args": [
                "-y",
                "@amap/amap-maps-mcp-server"
            ],
            "env": {
                "AMAP_MAPS_API_KEY": "96e6841038817fab25821697f44d15c8"
            }
        },
        "fetch": {
            "type": "sse",
            "url": "https://mcp.api-inference.modelscope.cn/sse/729c49665d834c"
        },
        "bing-cn-mcp-server": {
            "type": "sse",
            "url": "https://mcp.api-inference.modelscope.cn/sse/2aba790abd024b"
        },
        "txt-counter-practice": {
            "command": "python",
            "args": ["txt_counter_practice.py"],
            "port": 6274
        }
    }
}]
```

---

### 说明

- `"command": "python"` 和 `"args": ["txt_counter_practice.py"]` 表示用本地 Python 启动你的 MCP 服务（如果你已经手动启动，可以只保留 `"port": 6274`）。
- `"port": 6274` 指定了本地 MCP 服务监听的端口。
- 不要再用 `"type": "sse"` 和 `"url": ...` 这种云端SSE格式。

---

### 总结

1. 本地自定义MCP服务用 `"command"`、`"args"`、`"port"` 配置。
2. 云端/官方MCP服务用 `"type": "sse"` 和 `"url"` 配置。

请按上述方法调整 assistant_bot practice2.py 的 tools 配置，即可正常集成本地 txt 统计MCP服务！

如需进一步帮助（如多端口、多服务并存等），请继续提问！



![image-20250510103413654](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20250510103413654.png)

# 方法一为啥不成功



如果你希望像调用远程MCP（如Bing MCP）一样，通过SSE协议（即 `"type": "sse"` 和 `"url"`）来调用本地MCP服务，需要满足两个条件：

1. 你的本地MCP服务（如 txt_counter_practice.py）必须支持 SSE 协议（即返回 `Content-Type: text/event-stream` 的响应）。
2. 你的服务监听在本地端口（如 6274），并且可以通过 HTTP 访问。

如果你的本地MCP服务已经支持SSE协议（比如你用的MCP开发框架支持），你可以像这样配置：

```python
"txt-counter-practice": {
    "type": "sse",
    "url": "http://127.0.0.1:6274/"
}
```

这样配置后，Assistant会像调用远程SSE MCP一样，直接通过SSE协议访问你的本地服务。

---

## 关键点说明

- 如果你用 `mcp dev txt_counter_practice.py` 启动的服务**不支持SSE协议**（即它返回的是普通HTTP/HTML而不是`text/event-stream`），则不能用 `"type": "sse"` 方式，必须用 `"command"`+`"port"` 方式。
- 如果你**自己实现了SSE协议**，确保服务返回头部为 `Content-Type: text/event-stream`，且接口格式与云端MCP一致，就可以用 `"type": "sse"`+`"url"` 方式。

---

## 配置举例

### 1. 本地MCP支持SSE协议（推荐SSE方式时）

```python
"txt-counter-practice": {
    "type": "sse",
    "url": "http://127.0.0.1:6274/"
}
```

### 2. 本地MCP不支持SSE协议（推荐本地命令行方式）

```python
"txt-counter-practice": {
    "command": "python",
    "args": ["txt_counter_practice.py"],
    "port": 6274
}
```

---

## 总结

- **支持SSE协议**：用 `"type": "sse"` 和 `"url"`，像远程MCP一样调用。
- **不支持SSE协议**：用 `"command"`、`"args"`、`"port"`，让Assistant自动本地启动和调用。

---

如果你想让本地MCP像云端一样用SSE方式调用，但现在还不支持SSE协议，可以考虑升级你的MCP服务实现，或继续用本地命令行方式。

如需SSE协议的Python实现示例或MCP服务升级建议，请随时告知！



## 如果你希望像AMAP高德MCP那样用SSE协议（即 Assistant 通过 `"type": "sse"` + `"url"` 方式访问），你需要**有一个支持SSE协议的MCP服务端**。  
而`mcp dev txt_counter_practice.py`是开发调试用的，默认只支持本地HTTP，不支持SSE。

---

## 1. 如何让本地MCP支持SSE协议？

### 官方推荐的方式
你需要**将你的MCP服务注册到ModelScope云端**，由云端MCP代理SSE协议。  
本地开发阶段，**官方并未直接提供本地SSE服务的启动命令**，而是建议你用云端注册的方式。

### 方案一：注册到ModelScope云端
1. 登录[魔搭ModelScope](https://modelscope.cn/)。
2. 注册并上传你的MCP服务（如txt_counter_practice.py）。
3. 云端会分配一个SSE协议的URL，形如：
   ```
   https://mcp.api-inference.modelscope.cn/sse/你的服务ID
   ```
4. 在Assistant配置中用：
   ```python
   "txt-counter-practice": {
       "type": "sse",
       "url": "https://mcp.api-inference.modelscope.cn/sse/你的服务ID"
   }
   ```

### 方案二：本地自定义SSE服务（进阶/需自己开发）
- 你可以用`Flask`、`FastAPI`等框架自己写一个返回`Content-Type: text/event-stream`的SSE服务。
- 但这需要你自己实现SSE协议的推送格式，且Assistant的MCP客户端要能兼容。

---

## 2. 为什么AMAP高德MCP可以用SSE？
- 高德MCP官方已经在云端注册并部署，云端自动提供SSE协议接口。
- 你本地的`npx -y @amap/amap-maps-mcp-server`只是一个本地代理，实际数据流量走云端。

---

## 3. 推荐做法

- **开发调试阶段**：用`mcp dev txt_counter_practice.py`+`"command"`+`"port"`方式，最简单。
- **生产/云端SSE调用**：将服务注册到ModelScope云端，获取SSE URL。

---

## 4. 总结

- 本地开发：`mcp dev txt_counter_practice.py` + Assistant配置`"command"`+`"port"`
- 云端SSE：注册到ModelScope，Assistant配置`"type": "sse"`+`"url"`
- 本地SSE：需自己开发SSE服务（不推荐，除非有经验）

---

如需详细的云端注册流程或本地SSE服务开发示例，请告知！



# 还有什么办法能让自己开发的MCP server 通过网址和端口的方式被自己或者别人的程序调用呢？



当然有！你完全可以让自己开发的MCP server通过“网址+端口”的方式被自己或他人的程序调用。常见方式如下：

---

## 1. 作为标准HTTP/RESTful服务

### 方式说明
- 你开发的MCP server（如用Flask、FastAPI、Django、Tornado等Python Web框架）监听本地或服务器的某个端口（如 http://127.0.0.1:6274/ 或 http://你的公网IP:6274/）。
- 只要网络可达，任何支持HTTP请求的程序（Python、JavaScript、Postman、curl等）都可以通过URL+端口访问你的服务。

### 示例
假设你用Flask写了一个服务，监听在本地6274端口：

```python
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/count', methods=['GET'])
def count_txt():
    # 统计逻辑
    return jsonify({"count": 5})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6274)
```

- 你可以在本机或局域网/公网通过 `http://127.0.0.1:6274/count` 或 `http://你的IP:6274/count` 访问。

---

## 2. 让外部可访问（公网/内网穿透）

- 如果你希望别人（如同事、外部用户）也能访问，需要让服务暴露在公网。
- 你可以：
  - 部署到云服务器（如阿里云、腾讯云、AWS等），开放端口。
  - 使用内网穿透工具（如frp、ngrok、花生壳等）将本地端口映射到公网。

---

## 3. 作为MCP工具被Assistant等AI框架调用

- 只要你的服务是HTTP接口，Assistant等AI框架可以通过HTTP请求调用（如用requests库）。
- 你可以在Assistant的MCP配置中，直接写HTTP请求逻辑，或用`"type": "http"`+`"url"`（如果支持）。

---

## 4. 作为SSE服务（进阶）

- 如果你希望支持SSE协议（Server-Sent Events），需要返回`Content-Type: text/event-stream`，并按SSE格式推送数据。
- 这样可以被支持SSE的客户端（如部分AI平台、浏览器EventSource等）实时消费。

---

## 5. 作为通用API服务

- 你可以把MCP server当成普通API服务，写好接口文档，别人用HTTP库（如requests、axios、fetch等）就能调用。

---

## 6. 权限与安全

- 如果对外开放，建议加上API Key、Token、IP白名单等安全措施，防止被滥用。

---

## 总结

- 只要你的MCP server监听了IP和端口，并用HTTP协议，任何支持HTTP请求的程序都能通过“网址+端口”调用你的服务。
- 推荐用Flask/FastAPI等Web框架开发，部署到云服务器或用内网穿透工具暴露端口。
- 只要接口文档清晰，别人用Python、JS、Postman等都能直接访问。

---

如需具体的Flask/FastAPI服务示例、内网穿透教程或API安全建议，请随时告知！





# 在本地开发中将MCP Server集成到Qwen Assistant中

如果您是在本地开发环境中使用`from qwen_agent.agents import Assistant`，并希望将本地的MCP Server集成到Assistant中作为工具使用，可以按照以下步骤操作：

## 基本集成方法

1. **创建自定义工具类**：
   首先需要创建一个继承自`BaseTool`的自定义工具类来封装您的MCP Server功能

```python
from qwen_agent.tools.base import BaseTool

class MCPServerTool(BaseTool):
    name = 'mcp_server'
    description = 'A tool to interact with the local MCP Server'

    def __init__(self, mcp_server_url='http://localhost:port'):
        super().__init__()
        self.mcp_server_url = mcp_server_url

    def call(self, params: str, **kwargs) -> str:
        # 实现与MCP Server的交互逻辑
        import requests
        response = requests.post(
            f"{self.mcp_server_url}/api-endpoint",
            json={"input": params},
            headers={"Content-Type": "application/json"}
        )
        return response.json().get('result', 'No result')
```

2. **将工具注册到Assistant**：

```python
from qwen_agent.agents import Assistant

# 创建Assistant实例并添加您的工具
assistant = Assistant(
    tools=['code_interpreter', MCPServerTool(mcp_server_url='http://localhost:your-port')]
)
```

## 更完整的集成示例

```python
from qwen_agent.agents import Assistant
from qwen_agent.tools.base import BaseTool
import requests

class MCPServerTool(BaseTool):
    name = 'mcp_server'
    description = 'Interact with local MCP Server for specialized processing'
    
    def __init__(self, mcp_host='localhost', mcp_port=8000):
        super().__init__()
        self.base_url = f'http://{mcp_host}:{mcp_port}'
        
    def call(self, params: str, **kwargs) -> str:
        try:
            # 假设MCP Server有一个/process端点
            response = requests.post(
                f"{self.base_url}/process",
                json={"query": params},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('output')
        except Exception as e:
            return f"Error accessing MCP Server: {str(e)}"

# 使用示例
if __name__ == '__main__':
    # 初始化带有MCP工具的Assistant
    assistant = Assistant(
        name='My Assistant with MCP',
        description='An assistant with MCP Server integration',
        tools=[
            'code_interpreter',  # 保留原有工具
            MCPServerTool(mcp_port=8000)  # 添加您的MCP工具
        ]
    )
    
    # 运行对话
    while True:
        query = input("User: ")
        if query.lower() in ['exit', 'quit']:
            break
        response = assistant.run(query)
        print("Assistant:", response)
```

## 高级配置选项

1. **工具参数配置**：
   ```python
   assistant = Assistant(
       tools=[{
           'name': 'mcp_server',
           'url': 'http://localhost:8000',
           'api_key': 'your-api-key-if-needed',
           'timeout': 30
       }]
   )
   ```

2. **多工具集成**：
   ```python
   from qwen_agent.tools import DocParser, WebSearch
   
   assistant = Assistant(
       tools=[
           MCPServerTool(),
           DocParser(),
           WebSearch()
       ]
   )
   ```

3. **异步支持**：
   ```python
   import aiohttp
   
   class AsyncMCPServerTool(BaseTool):
       async def call(self, params: str, **kwargs) -> str:
           async with aiohttp.ClientSession() as session:
               async with session.post(
                   self.base_url,
                   json={"input": params}
               ) as response:
                   return await response.json()
   ```

## 调试技巧

1. 确保您的MCP Server正在运行并监听指定端口
2. 使用curl或Postman先测试MCP Server接口是否正常工作
3. 在工具类中添加日志记录：
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   
   def call(self, params: str, **kwargs) -> str:
       logging.info(f"Calling MCP Server with params: {params}")
       # ... rest of the code
   ```

4. 检查网络连接和防火墙设置，确保本地服务可访问

通过这种方式，您可以将本地开发的MCP Server无缝集成到Qwen的Assistant中，扩展其功能范围。





