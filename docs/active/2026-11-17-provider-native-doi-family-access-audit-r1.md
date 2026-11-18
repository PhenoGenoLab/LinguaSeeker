# provider-native DOI 家系候选访问审计 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**   
**PR:** 未合并

对 3 个高价值西语遗传性共济失调家系 DOI 使用 DOI resolver 和 pinned `lit-acquisition` 安全下载器进行有界访问探针：

- `10.33588/rn.3110.2000351`：SCA7 秘鲁家系
- `10.33588/rn.3302.2001057`：SCA8 家系
- `10.33588/rn.3808.2003624`：SCA7 墨西哥家系

结果为 **0/3 PDF**。每个 DOI 都保留 resolver URL、失败类型和 `confirmatory_admission=false`。失败表示当前全文链路不可用，不能编码为英文阴性或病例不存在。
