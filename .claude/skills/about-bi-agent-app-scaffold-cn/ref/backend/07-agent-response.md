# agent 说完之后, 到 UI 看到之前

> Strands 交回来的不是一个干净的答案, 是它自己构建的整个消息列表, 思考还内嵌在文本里.
> 这篇讲怎么从里面挖出 (thinking, answer), 以及为什么这三步必须一起走.

**对应代码**: `agent_app/agent_response.py` (生产), `agent_app/agent_debugger.py` (开发)

**依赖**: 无. `agent_response` 是纯字符串处理的叶子; `agent_debugger` 只依赖它.
使用者是 [09](09-http-entry-point.md).

---

## 为什么是两个文件

因为**解析在生产关键路径上, 打印不在**. `api/index.py` 每次回答都要解析; 而 `chat()` /
`print_summary()` 只有人在终端里跑脚本时才会走到.

把两者放在一个叫 "debugger" 的文件里, 结果是生产代码从"调试器"里 import 东西 —— 名字在骗
读者, 而且删调试辅助时没人敢动. 按读者切开之后:

| 文件 | 谁用 | 干什么 |
| :--- | :--- | :--- |
| `agent_response.py` | `api/index.py`, 以及调试器 | 解析. 纯函数, 不打印 |
| `agent_debugger.py` | 脚本和 REPL | 打印. 生产一行都不跑 |

---

## Strands 交回来的不是一个干净的答案

它交回的是它自己构建的**整个消息列表**, 而且:

- **思考还内嵌在文本里**, 是 `<thinking>...</thinking>` 标签
- **散在多条消息里**: agent 每调一次工具就产生一条 assistant 消息, 每条自带一个思考块
- **content 项不全是文本**: 调工具的那一轮里有 `{"toolUse": ...}` / `{"toolResult": ...}`

所以取答案要走三步, `parse_agent_response()` 是这三步的整体.

## 最后一条消息不一定是答案

这是最容易写错的一处, 而且写错了不报错.

取答案要取**最后一条"剥掉思考之后还剩东西"的 assistant 消息**, 而不是最后一条 assistant
消息. 因为一个先回答, 再调 `write_debug_report` 的 agent, 经常会用一条**只有
`<thinking>`** 的消息收尾 (内容大意是"最终答案已经给用户了").

无条件读最后一条消息的结果是: 答案为空, UI 渲染出一个思考块, 底下什么都没有 —— 在用户看来
就是卡住了.

## 三步必须一起走

```
extract_text_from_messages   消息列表  -> 一段带 <thinking> 的文本
parse_response_text          那段文本  -> (thinking, answer)
normalize_render_blocks      answer    -> 把 <chart> 标签改写成围栏
```

**它们合成一个 `parse_agent_response()`, 因为漏掉第三步是静默失败**: 答案照常到达, 只是图
没了. 所以不要在别处重新拼这三步 —— 调试路径少跑一步, 你在本地看到的就和生产不是同一个
东西.

## `normalize_render_blocks` 是什么补丁

提示词要求模型输出围栏块, 但小模型 (尤其 Nova Lite) 本来就在发 `<thinking>` 标签, 于是把
这个习惯泛化了, 把一段完好的 chart 载荷包进 `<chart>`. Markdown 把它当成未知 HTML 标签
直接丢掉, 于是回答里写着"这是图表", 下面什么都没有.

调提示词的措辞救不了这么小的模型, 而这个映射是无歧义的, 所以机械地做掉. 已经在围栏里的
内容不受影响: 那个正则要求标签独占一行.

`RENDERABLE_BLOCKS` 是[渲染契约](../architecture/06-rendering-contract.md)三半中的一半, 另外两半是
`components/chat/blocks/index.ts` 的查找表和 `data/system-prompt.md` 的指令. **加一种块要
三处一起改. **

## 空答案要说出来

`api/index.py` 在拿到空 answer 时会填一句话进去. 空答案会流出一个空文本块, UI 上就是一个
思考块底下什么都没有, 读起来还是"卡住了" —— **一个看得见的非答案可以排查, 沉默不行. **
