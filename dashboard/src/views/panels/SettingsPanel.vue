<template>
  <div>
    <div class="section-header">
      <h2 class="section-title">设置</h2>
      <p class="muted">环境变量与默认配置（只读）；任务级参数在「实验」页选择</p>
    </div>
    <div class="card card-pad">
      <ul class="settings-list">
        <li><strong>默认数据集</strong>：Fixture；可选 LoCoMo 10 persona</li>
        <li><strong>Pipeline 流程</strong>：Ingest → 可选 TiMEM Backfill（L2–L5）→ 仅 T0（推荐）</li>
        <li><strong>Full 流程</strong>：Ingest → T0 → T1（T1 自动 TiMEM backfill L2–L5，与 CLI 一致）</li>
        <li><strong>Ingest 等待 L2</strong>：实验页可勾选「Ingest 后等待 TiMEM L2」（默认关闭）；T0 检索仍会补 L2 安全网</li>
        <li><strong>手动 Backfill</strong>：实验/检索页「仅 TiMEM Backfill」；可勾选 L2–L5，写入 <code>backfill.json</code>（<code>mode: manual</code>），不影响 T1 默认层级</li>
        <li><strong>配置文件</strong>：<code>config/default.yaml</code>、<code>.env</code></li>
        <li><strong>TiMEM</strong>：<code>TIMEM_BASE_URL</code>（默认 <code>https://api.timem.cloud</code>）、<code>TIMEM_API_KEY</code>、<code>TIMEM_ACCOUNT_ID</code> — 在 <a href="https://api.timem.cloud" target="_blank" rel="noopener">api.timem.cloud</a> 注册并获取 API Key</li>
        <li><strong>MemOS</strong>：<code>MEMOS_API_KEY</code></li>
        <li><strong>Mem0</strong>：<code>MEM0_API_KEY</code>、<code>MEM0_BASE_URL</code></li>
        <li><strong>Judge</strong>：<code>ARK_API_KEY</code>、<code>JUDGE_MODEL</code></li>
      </ul>
      <p class="hint" style="margin-top: 16px">修改后需重启 <code>python main.py dashboard</code>。</p>
    </div>
  </div>
</template>
