# 配置: `.env` 和 `.env.defaults`

> 两个文件, 按**是不是密钥**切开. `.env` 装凭据, 不进 Git, AI 也打不开; `.env.defaults` 装
> 其余一切, 进 Git, 换数据集改的就是它. 这篇只讲怎么填, 为什么这么切见
> [architecture/07](../architecture/07-config-and-content.md).

**对应代码**: `.env.example`, `.env.defaults`, `agent_app/config.py`

---

## 起步

```bash
cp .env.example .env
```

然后在 `.env` 里填两样:

| 填什么 | 说明 |
| :--- | :--- |
| `DB_HOST` `DB_USER` `DB_PASS` `DB_NAME` | **必填**, 本地开发也一样. 用 Neon 的 `-pooler` 主机名 |
| **一个** LLM 凭据 | 只填 `LLM_PROVIDER` 指的那一个, 其余留着注释 |

`.env.defaults` 一般不用动 —— 它已经填好了, 而且进 Git.

---

## 两个文件装什么

| | `.env` | `.env.defaults` |
| :--- | :--- | :--- |
| 装什么 | API key, AWS 密钥, `DB_HOST/USER/PASS/NAME` | `SCHEMA_NAME`, `LLM_PROVIDER`, `LLM_MODEL_ID`, `AWS_REGION`, `DB_PORT`, 整块配额设置 |
| 是密钥吗 | **是** | 不是 |
| 进 Git | 不进 | **进** |
| AI 能开吗 | **不能**, `.claude/settings.json` 里 `deny` 了读和写 | 能 |
| 有模板吗 | `.env.example` | **没有, 它自己就是模板** |

**没有 `.env.defaults.example`, 这是故意的.** 那个文件进 Git, 所以它就是参考; 搞成
"gitignore 加模板"的话 `SCHEMA_NAME` 就跑到版本控制外面去了, 每次 clone 都要重填一遍.

---

## 优先级是三层

```
Vercel 的 Environment Variables      最高, 进程启动时就在 os.environ 里
        ↓
.env                                 本机的密钥和覆盖
        ↓
.env.defaults                        committed 的默认值, 补空缺
```

机制是一句话: `load_dotenv` **不覆盖已经设过的变量**, 而 `load_env_files()` 先读 `.env` 再读
`.env.defaults`.

**推论一**: `.env.defaults` 里的任何一行都能在单台机器上覆盖 —— 把同名 key 抄进 `.env` 即可.
比如让一个 checkout 指向 staging schema:

```bash
SCHEMA_NAME="acme_widgets_staging"
```

**推论二**: 部署时**只有密钥需要手填**. `.env.defaults` 进 Git, 跟着部署包一起上去, 所以
`SCHEMA_NAME` 这类值不用在 Vercel 面板里重录一遍.

---

## 三个填的时候会咬人的地方

**一, `"..."` 等于没设.** `.env.example` 里的占位符是 `"..."`, 而 `config.py` 的 `get_env()`
把这个值当成 unset. 所以从模板抄过来忘了注释掉的那一行不会变成一个"已设置, 非空, 但没用"
的变量.

**二, 用 bedrock 的话, 本地不要设 `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`.**
boto3 查环境变量**早于** `~/.aws/credentials`, 所以 `.env` 里一个占位符就能遮蔽一个好好的
本地 profile, 报出来的是
`UnrecognizedClientException: The security token included in the request is invalid` ——
一条完全指不到原因的错. 部署到 Vercel 时反过来: serverless 没有 `~/.aws`, 必须在面板里设.

**三, 换 `LLM_PROVIDER` 时记得 `LLM_MODEL_ID`.** 各家的 model ID 格式**不通用**. 要么一起改,
要么把 `LLM_MODEL_ID` 注释掉, 让它回退到那家的默认值.

换 provider **不需要重装依赖**: 四家 SDK 都是 `pyproject.toml` 里的核心依赖 (为什么不做成
extra, 见 [backend/02](../backend/02-config.md)).

---

## 打开月度花费上限

默认关着. 只有**付钱的人和打字的人不是同一个人**的公开部署才需要它.

打开要两步: `QUOTA_ENABLED="true"`, 外加 `DYNAMODB_TABLE_NAME_QUOTA` 指向一张你建好的
DynamoDB 表 (分区键必须是 `app_id`, 类型 String, 其余无所谓).

**只开一半会在启动时直接报错**, 不会拖到第一个用户提问 —— `Config.__post_init__` 里查这件事.

表名放在 `.env.defaults` 而不是 `.env`, 因为它**不是凭据**: 没有 IAM 权限它什么也给不了,
而且不像 `DB_HOST`, 它背后没有一个可以连的端点. 放这里是为了让"打开配额"是改一个文件而不是
两个. 不想提交表名的话放 `.env` 也行, `.env` 先读, 它赢.

配额本身怎么记怎么算, 见 [backend/05](../backend/05-quota.md).
