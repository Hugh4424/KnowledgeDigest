# GoInsight 过滤器术语表 / Filter Glossary
本页说明 filter field（过滤字段）在中英混排环境下的行为，请勿改写术语。
FAQ: 为什么 status=active 过滤后图表为空？
因为 chart type（图表类型）与 filter field 的枚举值必须同时匹配，缺一不可。
错误码 E_FILTER_17：过滤条件非法（invalid filter predicate），请检查参数拼写。
错误码 E_CHART_09：图表类型不支持该过滤器，Chart type does not support this filter。
参数 timeout：单位为秒（seconds），默认值 30，最大值 300。
参数 page_size：单位为条（rows），默认值 50，取值区间 [1, 500]。
术语对照：知识库 = knowledge base，溯源 = provenance，回写 = writeback。
注意——中文破折号、「全角引号」、（全角括号）以及顿号、分号；都必须原样保留。
参考 https://design.example/filter-cjk 获取完整的双语术语表。
