# LARK_AI_KNOWLEDGE_* 命令枚举（122 条）

本技能 v1 仅使用其中 4 条。完整清单见 `idl/improto.proto`。下表只列出与"问答主链路"相关的常用命令，便于扩展。

## 问答主链路（v1 已实现）

| Cmd | 名称 | 请求 → 响应 |
|-----|------|-------------|
| **1110001** | PUT_AI_ROUND | `PutAIRoundRequest` → `PutAIRoundResponse` |
| **1110002** | PUSH_AI_ROUND | (服务端推送) `PushAIRound` |
| **1110003** | PUSH_AI_ROUND_STREAMING_ANSWER | (服务端推送) `PushAIRoundStreamingAnswer` |
| **1110004** | PULL_AI_ROUND_STREAMING_ANSWER | `PullAIRoundStreamingAnswerRequest` → `PullAIRoundStreamingAnswerResponse` |
| **1110005** | PULL_AI_ROUNDS_BY_POSITION | `PullAIRoundsByPositionRequest` → `PullAIRoundsByPositionResponse` |
| **1110006** | PULL_AI_ROUNDS_BY_ID | `PullAIRoundsByIDRequest` → `PullAIRoundsByIDResponse` |
| **1110007** | PULL_AI_ROUND_RESOURCE | 拉取附件资源 |
| **1110008** | PUT_AI_FEEDBACK | 👍👎 反馈 |
| **1110011** | STOP_GENERATE | 停止生成 |
| **1110012** | PULL_AI_ROUND_COPY | 复制对话内容 |
| **1110013** | PUT_SHARE_LINK | 生成分享链接 |
| **1110014** | PULL_SHARE_LINK_CONTENT | 拉分享链接内容 |
| **1110016** | UPDATE_AI_ROUND_QUERY | 修改已发送 query |

## 话题管理

| Cmd | 名称 |
|-----|------|
| **1110101** | PUT_AI_TOPIC_READ — 标记已读 |
| **1110102** | PULL_USER_AI_TOPIC_LIST — 话题列表 |
| **1110103** | PULL_AI_TOPIC_BY_ID — 按 ID 取话题 |
| 1110104 | PUSH_AI_TOPIC_READ |
| 1110105 | DELETE_AI_TOPICS |
| 1110106 | PUSH_BATCH_AI_TOPIC |

## 用户/首页/Agent

| Cmd | 名称 |
|-----|------|
| 1110301 | PULL_USER_FEATURES |
| 1110401 | PULL_ONBOARD_QUERY_TEMPLATES — 首页示例 query |
| 1110402 | PULL_HOME_PAGE_INFO — 首页 |
| 1110403 | APPLY_FULL_FEATURE — 申请开通 |
| 1110501 | PULL_IDENTITY_PROFILE — 身份 |
| 1110502 | CHECK_USABLE — 是否可用 |
| 1110511 | PULL_SIDEBAR — 侧边栏 |
| 1110515 | PULL_WIKI_SPACE_DETAIL — 知识库 |
| 1110516 | PULL_AGENT_LIST — Agent 列表 |
| 1110517 | PUT_USER_AGENT_STATUS — 设置 Agent 状态 |

## 知识库管理

| Cmd | 名称 |
|-----|------|
| 1110512 | CREATE_DOCUMENT |
| 1110514 | PULL_OBJECTS_INDEX_STATE |
| 1110531 | RELEASE_WIKI_SPACE |
| 1110532 | CREATE_WIKI_SPACE |
| 1110533 | UPDATE_WIKI_SPACE_INFO |

## 索引/上传

| Cmd | 名称 |
|-----|------|
| 1120102 | GET_OBJECTS_INDEX_STATE |
| 1120103 | ENABLE_TENANT_KNOWLEDGE |
| **1120104** | PULL_USER_DATA_STATE — 用户数据状态（HAR 里抓到） |
| 1120106 | UPLOAD_SAMPLE_DOC_OBJECTS |
| 1120107 | PUT_USER_SETTINGS |

## 共享通用命令

| Cmd | 名称 |
|-----|------|
| **12001** | PULL_PACKETS_BY_SIDS — 长连接 sync（HAR 主流量） |
| 12002 | SYNC |
| 12003 | PULL_PIPELINE_INTERVAL_BY_SID |

完整 122 条见 `idl/improto.proto` 中 `LARK_AI_KNOWLEDGE_*` 与 `LARK_AI_*` 前缀的全部条目。
