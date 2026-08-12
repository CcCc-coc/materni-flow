# 写操作详解

本文档面向刚接触 AI Agent 开发的新手，解释为什么我们需要封装写操作，以及这个项目是怎么做的。

---

## 为什么这是"关键中的关键"？

到目前为止，我们的 AI Agent 只能**查数据**：
- "哪些床位是空的？" → 执行 SELECT 查询
- "今天有多少患者？" → 执行 SELECT 查询

但真正有用的 Agent 要能**做事情**：
- "把这个患者转到 201 床" → **修改**数据库
- "给这个患者创建一个高风险警报" → **插入**数据
- "安排明天的剖腹产手术" → **插入**医嘱

**能查询的是 Chatbot，能行动的才是 Agent。**

写操作就是让 Agent 从"只会说"变成"能做事"的关键。

---

## 为什么不能让 AI 随便写 SQL？

你可能会想：AI 能写 SELECT 查询，为什么不能让它写 INSERT/UPDATE？

**这样做非常危险！原因如下：**

### 1. AI 会"幻觉"

AI 可能生成看起来正确但实际错误的 SQL：

```sql
-- AI 想转移患者到 201 床
UPDATE admission SET bed_id = 201 WHERE patient_name = 'Julie';
-- 问题1: bed_id 应该是 UUID，不是数字
-- 问题2: patient_name 可能有重复
-- 问题3: 旧床位的状态没更新
-- 问题4: 新床位可能已经被占用
```

### 2. 缺少业务逻辑验证

转移患者不只是改一个字段。正确的流程是：
1. 检查患者是否存在
2. 检查新床位是否可用
3. 如果患者有旧床位，先释放旧床位
4. 更新新床位状态
5. 更新患者记录

AI 可能只做第 5 步，漏掉前 4 步，导致数据不一致。

### 3. 安全风险

如果 AI 能写任意 SQL，恶意用户可能诱导它执行：

```sql
DELETE FROM admission;  -- 删除所有患者记录！
DROP TABLE bed;         -- 删掉整个表！
```

### 4. 难以审计

随意生成的 SQL 难以追踪和审计。出了问题，你都不知道 AI 到底执行了什么。

---

## 解决方案：封装成函数

我们不让 AI 写 SQL，而是提供**预定义的函数**：

```python
# AI 不能这样做：
agent.execute_sql("UPDATE admission SET bed_id = ...")  # ❌ 危险

# AI 只能这样做：
assign_bed(admission_id="xxx", bed_id="yyy")  # ✅ 安全
```

**好处：**

| 问题 | 函数封装如何解决 |
|------|------------------|
| AI 幻觉 | 函数有明确的参数和验证 |
| 业务逻辑 | 函数内部实现完整流程 |
| 安全风险 | 只暴露允许的操作 |
| 审计追踪 | 每个函数调用都可记录 |

**类比理解：**

想象一个银行 ATM：
- ❌ 不会让你直接访问数据库改余额
- ✅ 只提供"取款"、"存款"、"转账"几个按钮

我们的写操作函数就是 AI 的"ATM 按钮"。

---

## 四个写操作函数

项目定义了 4 个写操作函数，位于 `write_operations.py`：

### 1. assign_bed() — 分配/转移床位

```python
def assign_bed(
    engine: sa.Engine,
    admission_id: str,
    bed_id: str,
) -> dict:
```

**功能：** 把患者分配到指定床位。如果患者已有床位，则先释放旧床位（转床）。

**业务逻辑：**
1. 检查患者（admission）是否存在
2. 检查目标床位是否存在且可用
3. 如果患者有旧床位 → 释放旧床位（状态改为 available）
4. 占用新床位（状态改为 occupied）
5. 更新患者记录（current_bed_id）

**使用场景：**
```
护士："急诊来了个临产患者，有空床吗？"
Agent："产房都满了。建议先安排到分诊区 triage-01。需要我现在分配吗？"
护士："好的。"
Agent：调用 assign_bed(admission_id=xxx, bed_id=triage_01_id)
```

---

### 2. update_prediction() — 更新出院预测

```python
def update_prediction(
    engine: sa.Engine,
    admission_id: str,
    predicted_los_hours: int,
    predicted_discharge_time: datetime,
) -> dict:
```

**功能：** 更新患者的预计住院时长和预计出院时间。

**业务逻辑：**
1. 验证预测时长在合理范围（6 小时 ~ 14 天）
2. 检查患者是否存在且未出院
3. 验证预计出院时间在入院时间之后
4. 更新预测字段

**使用场景：**
```
护士："203 床的陈女士刚做完剖腹产，什么时候能出院？"
Agent："陈女士剖腹产顺利，初产，无并发症。预计术后第 3 天出院，也就是周四。"
Agent：调用 update_prediction(admission_id=xxx, predicted_los_hours=72, ...)
```

---

### 3. create_alert() — 创建高风险警报

```python
def create_alert(
    engine: sa.Engine,
    admission_id: str,
    alert_type: str,      # high_bp, abnormal_fhr, fever, preterm_risk
    severity: str,        # warning, critical
    message: str,
) -> dict:
```

**功能：** 为患者创建一条高风险警报记录。

**业务逻辑：**
1. 验证 alert_type 是允许的类型之一
2. 验证 severity 是允许的级别之一
3. 检查患者是否存在且在院
4. 生成唯一 alert_id
5. 插入警报记录

**使用场景：**
```
护士："今天有哪些患者需要特别关注？"
Agent："两位需要注意：刘女士有妊娠高血压，今早血压上升趋势 (130→138→145)，
        建议增加监测频率。我已创建警报记录。"
Agent：调用 create_alert(admission_id=xxx, alert_type="high_bp", severity="warning", ...)
```

---

### 4. create_order() — 创建医嘱

```python
def create_order(
    engine: sa.Engine,
    admission_id: str,
    order_type: str,          # c_section, induction, epidural, lab_test, medication, consult
    scheduled_time: datetime,
    assigned_provider_id: str,
    priority: str = "routine",
    assigned_room_id: str = None,
    notes: str = "",
) -> dict:
```

**功能：** 创建一条医嘱记录（手术、检查、用药等）。

**业务逻辑：**
1. 验证 order_type 和 priority 是允许的值
2. 检查患者是否存在且在院
3. 检查医生（provider）是否存在
4. 检查手术室（room）是否存在（如有指定）
5. 生成唯一 order_id
6. 插入医嘱记录

**使用场景：**
```
护士："给 203 床王女士安排明天上午的剖腹产。"
Agent："我查了明天白班：外科医生 Smith 和麻醉师 Lee 都有空。
        产房 1 明早 9-11 点空闲。安排明早 9 点，产房 1？"
护士："好的。"
Agent：调用 create_order(admission_id=xxx, order_type="c_section", scheduled_time=..., ...)
```

---

## 代码实现要点

### 1. 参数化查询（防止 SQL 注入）

```python
# ✅ 正确：使用参数化查询
conn.execute(
    sa.text("SELECT * FROM bed WHERE bed_id = :bed_id"),
    {"bed_id": bed_id},
)

# ❌ 危险：字符串拼接
conn.execute(
    sa.text(f"SELECT * FROM bed WHERE bed_id = '{bed_id}'"),  # SQL 注入风险！
)
```

### 2. 事务（保证原子性）

```python
with engine.begin() as conn:
    # 这里的所有操作要么全部成功，要么全部回滚
    conn.execute(...)  # 操作 1
    conn.execute(...)  # 操作 2
    conn.execute(...)  # 操作 3
    # 如果操作 3 失败，操作 1 和 2 也会被撤销
```

**为什么需要事务？**

`assign_bed` 涉及 3 个更新：
1. 释放旧床位
2. 占用新床位
3. 更新患者记录

如果第 3 步失败，但 1 和 2 已经执行了，数据就乱了。事务保证"全部成功或全部失败"。

### 3. 输入验证

```python
valid_alert_types = {"high_bp", "abnormal_fhr", "fever", "preterm_risk"}

if alert_type not in valid_alert_types:
    raise ValueError(f"Invalid alert_type: {alert_type}")
```

只接受预定义的值，防止 AI 传入奇怪的东西。

### 4. 业务规则检查

```python
# 检查床位是否可用
if bed_row.status != "available":
    raise ValueError(f"Bed is not available: {bed_id}")

# 检查患者是否在院
if admission_row.status == "discharged":
    raise ValueError(f"Cannot create alert for discharged patient")
```

在执行操作前，先验证业务规则。

---

## 单元测试与幂等性

### 什么是幂等性？

**幂等性（Idempotence）** 是指：**同一个操作执行多次，结果和执行一次一样。**

**数学例子：**
- `abs(-5)` 执行 1 次 = 5，执行 100 次还是 5 → **幂等**
- `x + 1` 执行 1 次 = 6，执行 2 次 = 7 → **非幂等**

**为什么测试需要幂等性？**

假设你有一个测试：

```python
def test_create_alert():
    create_alert(admission_id="123", alert_type="high_bp", ...)
    # 验证数据库里有 1 条警报
```

第一次运行 ✅ 通过（1 条警报）
第二次运行 ❌ 失败（2 条警报，因为上次的还在）
第三次运行 ❌ 失败（3 条警报）

**测试结果不稳定！** 这就是非幂等导致的问题。

### 解决方案：备份恢复机制

我们的测试使用 `pytest fixture` 在每个测试前后备份和恢复数据库：

```python
@pytest.fixture(autouse=True)
def backup_and_restore_database():
    """每个测试前备份数据库，测试后恢复。"""
    db_path = path_enum.path_sqlite_db
    backup_path = db_path.with_suffix(".sqlite.backup")

    # 测试前：备份
    shutil.copy2(db_path, backup_path)

    yield  # 运行测试

    # 测试后：恢复
    shutil.copy2(backup_path, db_path)
    backup_path.unlink()  # 删除备份文件
```

**流程图：**

```
测试开始
    ↓
[备份数据库] → data.sqlite.backup
    ↓
运行测试（修改数据库）
    ↓
[恢复数据库] ← data.sqlite.backup
    ↓
测试结束（数据库回到原状）
    ↓
下一个测试开始（干净状态）
```

**好处：**
- 每个测试都从相同的初始状态开始
- 测试之间互不影响
- 可以反复运行，结果一致

### 测试结构

每个测试都遵循相同的模式：

```python
def test_assign_bed_to_patient():
    # 1. 读取数据，找到合适的测试对象
    admission_id = ...  # 找一个没有床位的患者
    bed_id = ...        # 找一个空床位

    # 2. 打印 BEFORE 状态
    print(f"[BEFORE] current_bed_id: {admission.current_bed_id}")

    # 3. 执行写操作
    result = assign_bed(engine, admission_id, bed_id)

    # 4. 验证 AFTER 状态
    assert admission_after.current_bed_id == bed_id
    assert bed_after.status == "occupied"

    # 5. 打印 AFTER 状态
    print(f"[AFTER] current_bed_id: {admission_after.current_bed_id}")
```

运行测试：

```bash
mise run test-python
```

---

## Agent 如何使用这些函数？

这些函数最终会被包装成 Agent 工具：

```python
# learn_smb_lending_lens/one/one_04_agent.py

@tool
def tool_assign_bed(admission_id: str, bed_id: str) -> str:
    """
    Assign or transfer a patient to a bed.

    :param admission_id: UUID of the admission record
    :param bed_id: UUID of the target bed
    """
    result = assign_bed(
        engine=one.engine,
        admission_id=admission_id,
        bed_id=bed_id,
    )
    return json.dumps(result)
```

AI Agent 看到的是这个工具的**文档字符串**，它会根据用户需求决定是否调用。

**完整流程：**

```
护士："把 Julie 转到 P-201-A 床"
           ↓
Agent 思考：需要调用 assign_bed 工具
           ↓
Agent 先查询：找到 Julie 的 admission_id 和 P-201-A 的 bed_id
           ↓
Agent 调用：tool_assign_bed(admission_id="xxx", bed_id="yyy")
           ↓
函数执行：验证 → 释放旧床 → 占用新床 → 更新记录
           ↓
返回结果：{"success": true, "message": "..."}
           ↓
Agent 回复："已将 Julie 转移到 P-201-A 床位。"
```

---

## 总结

| 概念 | 说明 |
|------|------|
| 为什么封装 | AI 不能随便写 SQL，需要预定义的安全操作 |
| 4 个函数 | assign_bed, update_prediction, create_alert, create_order |
| 参数化查询 | 防止 SQL 注入 |
| 事务 | 保证多步操作的原子性 |
| 输入验证 | 只接受预定义的值 |
| 幂等性 | 测试多次执行结果一致 |
| 备份恢复 | 保证测试环境干净 |

**核心思想：**

> **Agent 是眼睛和嘴巴；函数是手。**
>
> Agent 负责理解需求、决定行动；
> 函数负责安全地执行操作。
>
> 这种分离设计是生产级 AI 系统的关键。
