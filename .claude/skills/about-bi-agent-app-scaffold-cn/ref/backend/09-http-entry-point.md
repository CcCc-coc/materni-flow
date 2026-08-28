# 一次 `/api/chat` 请求的完整生命周期

> 这篇讲 `api/index.py` —— 后端唯一的 HTTP 边界. 它自己不做任何业务, 只把前面几篇的零件
> 按顺序串起来. 但这个顺序里有四个决定是踩出来的, 换个顺序就会静默地出错或者多花钱.

**对应代码**: `api/index.py`

**依赖**: 几乎全部 —— `vendor/vercel_ai_sdk`, `ai_sdk_adapter`, `agent_response`, `quota`,
`one`, `utils`. 它在 `agent_app/` **外面**, 因为它是部署产物 (Vercel 按 `api/` 目录发现
serverless function), 不是这个包的一部分.

---

## 两个端点

| 路由 | 干什么 |
| :--- | :--- |
| `GET /api/hello` | 健康检查. 存在的意义是"FastAPI 起来了"和"整条链路挂了"这两件事能分开 |
| `POST /api/chat` | 全部业务 |

---

## `/api/chat` 的九步

```
1. read_request_body        读 body, 顺便记一条脱敏过的请求日志
2. RequestBody(**data)      宽松解析成 AI SDK 的数据模型
3. get_last_user_message    取出这一轮要回答的问题;  空 -> 直接返回错误流
4. agent.messages.clear()   清空, 然后灌入前端送来的历史
5. check_quota              花钱之前拦一次
6. agent(question)          调模型, 期间把 stdout 顶掉
7. increment_usage          按这一轮真实的 token 数记账
8. parse_agent_response     从消息列表里挖出 (thinking, answer)
9. ai_sdk_streaming_response  编码成 SSE 还给前端
```

前三步和最后一步在 [06](06-frontend-protocol.md), 第八步在 [07](07-agent-response.md),
第五和第七步在 [05](05-quota.md). 这篇只讲**顺序本身**里的决定.

---

## 决定一: 每次请求都把 agent 的记忆清空重建

```python
agent = one.agent
agent.messages.clear()
agent.messages.extend(request_body_to_agent_history(request_body))
```

看起来浪费, 其实是必须的, 而且理由有两层.

**`one.agent` 是 `cached_property`**, 所以一个进程里只有一个 Agent 实例, 它会跨请求活着.
不清空的话, 第二个用户会读到第一个用户的对话.

**真正的对话状态在前端.** AI SDK 的 `useChat()` 每次都把完整消息列表 POST 上来, 所以后端
是**无状态的** —— 这正是它能跑在 serverless 上的原因: 任何一个实例都能接任何一个请求.

所以这三行的含义是: 把这个进程里的残留状态**丢掉**, 换成这次请求自带的那份真相.

---

## 决定二: 配额拦在调模型之前

```python
try:
    check_quota(one.dynamodb_client(), one.config)
except QuotaExceededError as e:
    return ai_sdk_streaming_response(QUOTA_EXCEEDED_MESSAGE)
```

**拒绝路径一分钱不花**: 返回的是一条写死的常量文案, 不是让模型去生成一句道歉.

位置也是有讲究的 —— 它在**灌完历史之后, 调模型之前**. 更早的话拿不到解析结果, 更晚就已经
付过钱了.

`check_quota` 自己会检查 `quota_enabled` 并提前返回, 也自己咽掉基础设施故障, 所以这里不用
包 `if`, 也不用包 `except Exception`. 能走到 `except QuotaExceededError` 的只有一种情况:
真的超了. 这条边界属于 [05](05-quota.md).

---

## 决定三: 计量读 `agent_invocations[-1]`, 不读 `accumulated_usage`

```python
invocations = getattr(agent_result.metrics, "agent_invocations", None) or []
usage = invocations[-1].usage if invocations else {}
```

**这是一个会静默多计费的坑.** `metrics.accumulated_usage` 是 strands 在**这个 Agent 实例的
生命周期内**累计的. 而 `one.agent` 是缓存的, 一个进程能服务上千个请求 —— 读它就等于每次
都把之前所有请求重新记一遍账, 配额会以平方级的速度烧完.

要的是**这一轮**的用量, 它在最新那个 `AgentInvocation` 上.

`getattr(..., None) or []` 这层保护是给 strands 版本变化留的: 拿不到用量应该记零, 不该让
一个已经生成好的回答失败.

---

## 决定四: 调 agent 时把 stdout 顶掉

```python
old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    agent_result = agent(last_user_message)
finally:
    sys.stdout = old_stdout
```

strands 默认会把流式输出打到 stdout. 而**在 Vercel 上 stdout 是响应流的一部分** —— 打到
那里的东西会直接混进发给浏览器的字节里, 把 SSE 流搅坏.

`finally` 不能省: agent 抛异常时 stdout 也要还回去, 否则这个进程后续所有请求的日志都进了
一个没人读的 `StringIO`.

同样的理由, 这个仓库的 `debug()` 打 **stderr** (见 [01](01-leaves.md)).

---

## 空答案要说出来

```python
if not answer:
    answer = "I worked through this but did not produce a final message. ..."
```

agent 有可能只留下思考, 没有最终文本 (为什么会这样见 [07](07-agent-response.md) 里"最后
一条消息不一定是答案"). 这时候流一个空文本块出去, UI 上就是一个思考块底下什么都没有 ——
在用户看来就是卡死了.

**一个看得见的非答案可以排查, 沉默不行.** 所以这里填一句话, 并且记一条 debug 日志.

---

## 这个文件不该长什么样

它是**组装点**, 不是业务层. 判断一段代码该不该待在这里:

- 它是否知道两个以上模块的内部细节? 是 -> 它属于其中一个模块, 不属于这里
- 它是否会被第二个调用方需要? 是 -> 抽成函数放进 `agent_app/`

这条规矩是补回来的. 这个文件曾经在三个地方各拼了一遍 `StreamingResponse(...)` 加三行
SSE header, 也曾经在两处各写一遍 `if one.config.quota_enabled:` —— 两次都是把某个模块的
知识漏到了使用者这里, 而且第二个使用者忘了抄就是一个 bug. 现在 header 跟着 generator 走,
开关跟着 quota 走, 这个文件只剩顺序.
