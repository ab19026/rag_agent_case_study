PROMPT_DELIMITER="\n"
AGENT_REFUSAL = {
    'zh' : '问题不合规,拒绝回答',
    'en' : 'Question non-compliant, refuse to answer.'
}
MODEL_USAGE_AGENT = 'agent'
MODEL_USAGE_RERANK = 'rerank'
MODEL_USAGE_EMBEDDING = 'embedding'
# 其它功能(总结、合规等)依然复用agent模型
MODEL_USAGE_SUMMARY = 'agent'
MODEL_USAGE_QUERY_ENHANCE = 'agent'
MODEL_USAGE_COMPLIANCE = 'agent'
MODEL_USAGE_STYLE_CONSISTENCY = 'agent'