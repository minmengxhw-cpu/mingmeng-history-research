# 《民主周刊》第八期身份视觉核验

日期：2026-08-21

## 结果

对 CADAL 03016374（目录题名为《民主周刊》第八期，1946 年 6 月）完成了三个公开页图预览的只读视觉核验：第 1 页、第 2 页和第 20 页。第 1 页明确显示《民主周刊》和“第八期”；第 2 页为正文内页并可见印刷页码“2”；第 20 页为可访问的末页正文影像。单期文件本身登记为 20 页，SHA256 为 `5ba6e7db4d7ee5b0ef4ea495b4b83aec902198150cfd9be6295dce0d4ff740b2`；三个公开页图预览的 SHA256 已写入机器记录。

这完成了 G1 的“期号身份”门槛，但没有完成正文引用门槛：本轮没有转录文章、没有把 OCR 草稿写入正式 SQLite，也没有把该单期在 1279 页合订册中的物理页范围当成已知事实。

## 分层结论

- `identity_status=ISSUE_IDENTITY_CONFIRMED`；
- `page_identity_status=human_verified_identity_only`；
- `citation_ready=false`；
- `formal_db_apply=false`；
- 后续允许进入期号导航和定向 OCR 队列。

机器记录见 [`ISSUE_IDENTITY_REVIEW.json`](./ISSUE_IDENTITY_REVIEW.json)。
