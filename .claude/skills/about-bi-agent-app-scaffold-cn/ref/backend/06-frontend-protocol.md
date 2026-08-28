# 前端协议: 请求怎么进来, 回答怎么出去

> 前端和 agent 描述"一段对话"的方式不一样, 这两个文件是唯一同时懂两边的地方. 进来的是
> AI SDK 的 `RequestBody`, 出去的是 SSE 上的 AI SDK v5 Data Stream Protocol.

**对应代码**: `agent_app/vendor/vercel_ai_sdk.py` (数据模型), `agent_app/ai_sdk_adapter.py`
(翻译和编码)

**依赖**: `utils` ([01](01-leaves.md)). vendor 那个文件零依赖. 使用者是
[09](09-http-entry-point.md).

---

## 两个文件, 分工不能混

| 文件 | 是什么 |
| :--- | :--- |
| `vendor/vercel_ai_sdk.py` | **纯数据模型**. 前端 POST 上来那个 JSON 的 pydantic 镜像 |
| `ai_sdk_adapter.py` | **翻译和编码**. 模型 <-> agent 消息, 以及回程的 SSE |

---

## vendor: 为什么是拷进来的, 为什么故意宽松

它 vendor 自 `vercel-ai-sdk-mate`, **拷进来而不是装依赖**, 两个理由: 它是 100 行 pydantic
模型, 不值得为它引入一个我们控制不了发版节奏的依赖; 而下面那条前向兼容行为是我们加的, 不是
上游的.

**前向兼容是这个文件的全部设计目标.** AI SDK 是一个跑得很快的前端库, 它会不断加新的 message
part 类型和新字段. 一个严格校验的后端会在**别人跑一次 `pnpm update` 的那天**开始拒绝完全
合法的流量 —— 而且是在 Python 这边失败, 离引发它的改动十万八千里.

所以它遵守那条老规矩: **对读的东西严格, 对不读的东西宽容.**

- 后端真正会读的字段 (`messages`, 每个 part 的 `type` 和 `text`) 有类型, 缺了就报错
- 其余一切多出来的字段被接受并忽略
- 不认识的 part 类型不会炸, 只是解析成一个通用的壳

**什么时候要改它**: 后端开始需要读一种新的 part 类型时 —— 加一个模型类, 在
`PART_MODEL_BY_TYPE` 里加一行. 就这两步.

**什么时候不该改它**: 任何 provider 相关的东西. 这个文件里出现 Bedrock / OpenAI / Strands
的痕迹, 就意味着换 provider 要动前端契约, 而这两件事毫无关系.

---

## 两种方言, 一个地方知道两种

前端和后端描述"一段对话"的方式不一样, 这个模块是唯一同时懂两边的地方.

**进来的**: 前端 POST 一个 `RequestBody`, 它的每条消息是一串带类型的 *part* (text,
reasoning, ...). agent 要的是 content 为 `[{"text": ...}]` 的消息.

**出去的**: agent 交回一个已经写完的字符串. 前端要的是 AI SDK v5 Data Stream Protocol,
走 Server-Sent Events.

**这里没有任何 provider 相关的东西.** agent 用的那个消息格式恰好是 AWS 为 Bedrock Converse
API 发明的, Strands 在它支持的所有 provider 上都沿用了它 —— 所以 `LLM_PROVIDER` 在
bedrock / openai / anthropic / google 之间切换, 不碰这个文件. **要保持这样**: 真需要
provider 相关代码时, 它属于 `one_04_agent.py` 里构造 model 的地方, 不属于这里.

---

## SSE 协议长什么样

每个事件是一行 `data: <json>`, 后面跟一个空行. 文本和 reasoning 各自是**三段式** ——
start / delta / end —— 这样 UI 能开一个块, 填它, 关掉它.

```
data: {"type": "reasoning-start", "id": "..."}

data: {"type": "reasoning-delta", "id": "...", "delta": "..."}

data: {"type": "reasoning-end", "id": "..."}

data: {"type": "text-start", "id": "..."}

data: {"type": "text-delta", "id": "...", "delta": "..."}

data: {"type": "text-end", "id": "..."}

data: {"type": "finish", "finishReason": "stop"}

data: [DONE]

```

几个不能省的细节:

- **每个块要有 id**, 前端靠它区分并发的块, 并把每个 delta 匹配回它所属的块
- **`finish` 事件不能少**, 少了 UI 会一直转圈
- **`[DONE]`** 是协议定义的流终止标记, 不是我们自己发明的
- **reasoning 为空时整段跳过**. 一个空块在 UI 上是一个点开什么都没有的折叠箭头

这里**一个 delta 装完整个字符串**, 因为走到这一步 agent 早就写完了. 真正的逐 token 流式
会发很多个 delta, 协议的其余部分一个字不用改.

---

## 那三个 HTTP header 也是协议的一部分

```
x-vercel-ai-ui-message-stream: v1
Cache-Control: no-cache
Connection: keep-alive
```

第一个是 AI SDK 用来识别这是 v5 message stream 的; 少了它前端不会按这个协议解析. 后两个是
让代理和浏览器别缓冲这个流.

**它们和 generator 住在一起** (`ai_sdk_streaming_response`), 不由调用方拼. 让每个返回流的
地方各拼一遍 `StreamingResponse(...)` 加三行 header, 等于把协议的一部分交给使用者保管: 协议
改了要同时改每一处, 而漏掉一处的症状是**前端静默地不渲染**.

---

## reasoning 不进历史

`request_body_to_agent_history` 把 reasoning part 丢掉. agent 重读自己之前的思考没有好处,
而那些块很长 —— 留着的话每一轮都会重发一次, 并且付一次钱.

同样地, **最后一条消息被排除在历史之外**: 那是现在要回答的问题, 它作为 agent 的输入进去,
不作为历史.

没有任何文本的消息会被跳过, 而不是发一条空 content —— provider 会拒.

---

## 请求日志里的 header 要脱敏

`read_request_body` 会把请求头打进日志. **`authorization` / `cookie` 这类必须打成
`<redacted>`** —— 这些日志在 Vercel 上是留存的, 把凭证写进去等于把它泄漏到一个谁能看日志
谁就能看到的地方.

这个函数既记日志又返回 body, 是因为**一个请求体只能读一次**: 在这里读了再扔掉, 调用方就
没东西可解析了.
