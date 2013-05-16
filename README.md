### 项目介绍

大家都为给类和变量起名烦恼过吧，我想给一些开源项目做个分词，提取一些常用的好名字出来做参考，大家推荐一些名字起得好的开源项目吧。

### 基本设计
1. 首先有个CodeScanner来获取一个目录下的源码文件
1. 再有个TokenScanner把某个文件里的标识符提取出来，我的不严谨的万能分词算法终于用上了
1. 再有个KeywordFilter把各语言的关键字过滤掉
1. 最后用TokensHandler把过滤后的token进行计数，并按出现次数倒序排列
1. 大概就是TokensHandler(KeywordFilter(TokenScanner(CodeScanner(project_dir))))
