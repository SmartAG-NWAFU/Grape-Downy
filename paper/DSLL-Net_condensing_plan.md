# DSLL-Net 论文精简建议

## 当前判断

论文主线清楚：DSLL-Net 将葡萄霜霉病严重度估计拆成叶片分割和病斑分割两个阶段。第一阶段用 SimAM-MobileNetV3 + DeepLabV3+ 提高复杂田间背景下的叶片分割效率；第二阶段用 SimAM-EfficientNet-B0 + RepConv U-Net 提高小病斑和边界分割；最终用病斑面积 / 叶面积估计严重度，并通过 Android 应用展示部署潜力。

当前全文约 9000 词。投稿前建议目标压缩到 6500-7500 词。优先保留创新点、数据集、关键模型结构、核心指标和部署验证，删减文献罗列、模块原理解释、重复性讨论和过细的实验设置描述。

## 章节压缩优先级

1. Introduction：建议从约 840 词压缩到 550-650 词。
   - 合并传统人工评估、分类方法和分割方法的背景。
   - 删除逐篇列举准确率的长句，只保留“classification is coarse; single-stage segmentation causes leaf-lesion interference; dual-stage methods still face efficiency/deployment limits”。
   - 末段贡献建议改成 3 个清晰贡献点。

2. Materials and Methods：建议从约 3000 词压缩到 2100-2400 词。
   - Workflow、Data preparation、Experimental design 可合并部分重复说明。
   - Leaf model 和 lesion model 中，保留结构差异和原因，删去 MobileNetV3、EfficientNet-B0、SimAM、RepConv 的通用原理性介绍。
   - Evaluation metrics 可压缩为一段文字加公式，避免每个指标后再解释一遍。
   - 表格如果已经列出训练设置，正文不再重复参数。

3. Results：建议从约 1600 词压缩到 1100-1250 词。
   - 每个结果小节只写“best model + key metric + comparison implication”。
   - 删除对图表中每个模型的逐项复述，把细节留给表格和图。
   - App/专家评估结果只保留与严重度估计有效性相关的关键指标。

4. Discussion：建议从约 1400 词压缩到 850-1000 词。
   - 叶片分割、病斑分割、双阶段优势三段可以合并为“why it works”。
   - 删除与 Introduction 重复的农业意义开头。
   - 删除对 EfficientNet、SimAM、RepConv 的二次原理解释。
   - Practical deployment 保留 1 段；Limitations 保留 1 段。

5. Conclusion：约 190 词，可压缩到 130-150 词。
   - 只保留方法、关键性能、意义和未来扩展。

## 建议保留的核心信息

- Problem：field disease severity estimation is difficult because leaf area and lesion area must both be accurate under complex backgrounds.
- Gap：single-stage models suffer feature interference; existing dual-stage models often overlook compactness and deployment.
- Method：two-stage pipeline: SimV3-DL3+ for leaf segmentation; SimEffB0-RepUNet for lesion segmentation.
- Evidence：lesion IoU = 74.3%, parameters = 12.56 M, severity agreement R2 = 0.976.
- Practical value：lightweight deployment and Android application for field disease monitoring.

## 可直接替换的精简 Abstract 示例

Quantitative disease severity assessment from field images requires accurate estimation of both leaf and lesion areas, but complex backgrounds, illumination variation, occlusion, and small lesion patterns remain challenging. This study proposes DSLL-Net, a lightweight dual-stage leaf-lesion segmentation framework for grapevine downy mildew severity quantification. DSLL-Net first segments leaves using DeepLabV3+ with a SimAM-enhanced MobileNetV3 backbone, and then delineates lesions with an improved U-Net integrating a SimAM-EfficientNet-B0 encoder and a RepConv decoder. This task decomposition reduces feature interference between leaf boundaries and disease symptoms while maintaining computational efficiency. Experiments on field datasets show that DSLL-Net achieves a favorable accuracy-efficiency trade-off, with a lesion IoU of 74.3% using 12.56 M parameters. Severity estimates derived from segmented leaf and lesion areas strongly agree with reference values (R2 = 0.976). The framework was further integrated into an Android application, demonstrating its potential for field-oriented disease monitoring and decision support.

## 可直接替换的精简 Introduction 末段贡献写法

In this study, we propose DSLL-Net, a lightweight dual-stage framework for quantitative grapevine downy mildew severity assessment from field images. The main contributions are: (1) a task-decoupled leaf-lesion segmentation pipeline that reduces interference between leaf boundaries and small lesions; (2) a compact leaf segmentation model based on SimAM-MobileNetV3 and DeepLabV3+ and an efficient lesion segmentation model based on SimAM-EfficientNet-B0 and RepConv U-Net; and (3) a severity estimation and mobile deployment workflow validated under field conditions.

## 可直接替换的精简 Discussion 框架

The results demonstrate that separating leaf and lesion segmentation is effective for disease severity quantification under field conditions. The leaf segmentation stage provides a reliable denominator for severity calculation, while the lesion segmentation stage focuses on small and irregular symptomatic regions. Compared with single-stage models, this decomposition reduces feature interference and improves the stability of severity estimation.

The performance gains arise from the complementary roles of lightweight backbones, attention, and structural re-parameterization. SimAM improves spatial sensitivity without adding parameters, helping both leaf boundary extraction and lesion localization. EfficientNet-B0 improves lesion feature representation with limited model size, while RepConv strengthens boundary refinement during training and preserves inference efficiency after re-parameterization. As a result, DSLL-Net achieves a strong accuracy-efficiency balance and supports practical deployment.

The framework also has limitations. It uses two networks, so inference can still be slower than some single-stage alternatives. The current evaluation focuses on one crop-disease system, and broader validation across crops, diseases, sensors, and field environments is needed. Pixel-level annotation remains labor-intensive; semi-supervised or weakly supervised learning may reduce this cost in future work.

## 语言层面统一删减规则

- 删除或替换高频空泛短语：robust and quantitative, favorable accuracy-efficiency trade-off, practical field deployment, real-world agricultural environments。每节最多保留一次。
- 避免同一句中连续出现 3 个以上形容词，例如 accurate, scalable, robust, efficient, practical。
- 图表结果不要逐项复述。正文只写最关键结论，例如 “SimV3-DL3+ achieved the best balance between mIoU and parameter count (Table X).”
- 方法模块不要重复解释已有经典网络的背景，只说明为什么在本研究中使用以及带来什么变化。
- Discussion 不再重复 Introduction 的问题背景，直接解释结果和机制。
