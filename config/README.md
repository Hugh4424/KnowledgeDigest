# 配置目录

这里仅保留当前命令或当前 acceptance 入口会直接读取的配置：

- `knowledge-digest.json`：项目默认配置样例；
- `task0-question-set.v1.json`：只读对比脚本使用的固定题集；
- `task4-source-coverage-89-input.v1.json`：语义编译默认来源清单；
- `task5-publication-layout-v2.json`：当前发布布局合同；
- `task5-quality-cases-v2.json`：当前质量运行题集；
- `task7-topic-map.json`：语义编译默认主题映射；
- `task9-comparison-mapping.v1.json`：当前查询集验收的显式对照映射。

Task4/Task5/Task10 的历史 mapping、旧合同、旧题集和旧验收输入位于
`config/archive/`，不会被默认命令隐式加载。需要重放历史实验时，必须显式传入归档路径，避免把历史材料误当作当前运行输入。
