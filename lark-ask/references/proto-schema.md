# 关键消息 Schema

来源: `idl/ai_knowledge.proto` + `idl/ai_topic_stream_search.proto`

## PutAIRoundRequest（cmd 1110001 — 发起问答）

```proto
message PutAIRoundRequest {
  optional int64 ai_topic_id = 1;     // 不传 → 服务端新建 topic
  optional string cid = 2;            // 客户端 uuid，去重
  optional QueryContent query = 3;    // 用户 query
  optional bytes qa_ai_topic_request_info = 4;
  optional AIRoundContext ai_round_context = 5;
  optional int64 ai_round_id = 6;
  optional SceneInfo scene_info = 7;  // 不传 → ASK_SCENE_MAIN_TOPIC
  optional bool invisible = 8;
  optional AIGenIDInfo ai_gen_id_info = 9;
  optional AgentType agent_type = 10;
  optional int64 parent_topic_id = 11;
}

message QueryContent {
  optional string content = 1;        // **核心字段，Markdown 文本**
  repeated Resource resources = 2;
  // ... link_preview, rich_text, quote_block
}
```

## PullAIRoundStreamingAnswerResponse（cmd 1110004）

```proto
message PullAIRoundStreamingAnswerResponse {
  optional int64 ai_round_id = 1;
  oneof ai_round_answer {
    AIAnswer ai_answer = 2;     // 中间包：流式 chunk
    AIRound ai_round = 3;       // 终态包：完整 round
  }
  optional AIRoundStatus ai_round_status = 4;
}
```

`AIAnswer.content` 是 `bytes`，反序列化为 `AnswerCard`：

```proto
message AnswerCard {
  optional QueryUnderstandingBlock query_understanding_block = 2;
  optional AnswerBlock rag_answer_block = 3;        // **主答案 Markdown**
  optional AnswerBlock doubao_answer_block = 4;     // 外网搜索答案
  repeated Reference reference_block = 6;           // 引用列表
  // ...
}

message AnswerBlock {
  optional string markdown = 1;   // **核心：增量 markdown 文本**
  optional Status status = 2;     // STREAMING / FINISHED / ERROR / REASONING
  optional string reasoning = 3;
  // ...
}
```

## AIRoundStatus 枚举

| 值 | 名称 | 何时收到 |
|----|------|----------|
| 1 | INITIAL | 刚提交 |
| 2 | STREAMING | 流式中（继续轮询） |
| **3** | **FINISH** | **正常结束（停止轮询）** |
| 4 | STOPPED | 用户中断 |
| 5 | ERROR | 失败 |
| 6 | PENDING | 等待用户确认 |

## AskScene 枚举（SceneInfo.ask_scene）

| 值 | 名称 | 适用场景 |
|----|------|----------|
| 1 | ASK_SCENE_MAIN_TOPIC | **默认主对话**（v1 用） |
| 2 | ASK_SCENE_WIKI_TOPIC | 知识库内 |
| 3 | ASK_SCENE_MINUTES | 妙记内 |
| 6 | ASK_SCENE_DOC | 文档 AI |
| 7 | ASK_SCENE_IM | IM 内问答 |

## PullUserAITopicListRequest（cmd 1110102）

```proto
message PullUserAITopicListRequest {
  optional int32 page_count = 1;        // 服务端最多 50
  optional int64 offset_timestamp = 2;  // 0=首页，否则上一页最后 update_time
  repeated SceneInfo scene_infos = 4;   // 按场景过滤
  optional PullDirection pull_direction = 5;
  optional bool need_deleted = 6;
}

message AITopic {
  optional int64 id = 1;
  optional string name = 2;
  optional int32 last_round_position = 4;
  optional int32 unread_count = 5;
  optional int64 create_time_ms = 249;
  optional int64 update_time_ms = 250;
  // ...
}
```
