# IMR Press SCA2 家系 PDF 恢复 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**   
**PR:** 未合并

通过 IMR Press DOI 页面提取 storage PDF URL，恢复 `10.33588/rn.27160.98290`。原文为西语 SCA2 家系/亲属纵向研究：59 名患者子女、10 年四次研究，79 名亲属中 17 人出现临床体征；同时提供电生理、神经传导和随访维度。

机器可读工件：[SCA2 recovery](../../benchmark/experiments/acmg_multilingual/candidate_audits/multilingual_provider_native_round3_20261117/imrpress_sca2_family_r1/)。

该记录形成 5 条可定位引文，观察患者 17、家系 1；由于提取文本未直接呈现患者级 CAG 变异写法，`variant_event=null`，不把遗传背景描述补成患者变异事件。
