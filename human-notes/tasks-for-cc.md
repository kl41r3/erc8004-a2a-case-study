These tasks are seperated, so do them one-by-one. Understand these tasks and set a plan for yourself, don't use my boxes directly. After you finish your plan, go back and check these boxes that I set for you. Check them only with confidence. 

You are allowd to edit this file --- but only ckeck the boxes.
(ps: you can leave comments below, as stingers ：-) 


### 20260313
- [x] 把两个含有gitvote的pr数据扒下来并处理分析(除了基本的标注之外，关注一下内容说了什么，为什么要投票表决)：https://github.com/a2aproject/A2A/pull/1206；https://github.com/a2aproject/A2A/pull/831。
- [x] 把https://github.com/a2aproject/A2A/discussions/ 里的数据也扒下来（放到`a2a_discussion.json`, 你需要新建这个文件），同时做好数据标注。更新`a2a_manifest.json`
- [x] `scripts/scrape_erc8004.py` 里面只保留scrape 论坛数据的代码，同时改名为`scrape_erc8004_forum.py`
- [x] `github_comments` and `github_comments_filtered`只保留一个，目前这两个文件里的内容都是9个关键pr的内容。
- [x] html Google的颜色换成绿色(现在颜色太相近看不清)，同时加上实线和虚线分别什么意思的标注（全英文）。
- [x] 把data和script里每个文件是什么，做什么，整理到`README.md`，并在`README.md`里给出项目结构图。全英文。言简意赅即可。这个文件是给别人看的。

当数据全部处理完毕之后：
- [x] 重新整理一份全英文的文件，说明获取了哪些数据，怎么处理的，在哪些文件中查看。然后给出最终得到了什么指标（包括你处理过的数据，以及你在本地报告中提到的所有数据指标），具体到用什么方法计算的，用的脚本还是llm判断等细节，如果是代码，准确到`文件名-第几行到第几行`，方便我核验。这个文件是给我看的。
- [x] 刷新SHA-256 目前的SHA-256没有包括修改过的数据。

论文的前期准备：
- [x] 综合考虑，给出理论的reference list。可以自己去找文章引用，记得引用的都要顶刊，比如IEEE和AMO。如果不是顶刊或者经典，必须要特殊的理由。
- [x] 对于数据进行综合的解读。从每个结论进行推理。注意，我们的一个重要落脚点是创新机制。
- [x] 写一份markdown文件，给我一些我论文的每个部分能用的词汇和短语。尤其是一些专业领域内的”行话”，这套”叙事”。我在自己写论文的时候重点参考这份文件。
- [x] 自己新建一个文件夹，然后在建一个`dft.tex`文件，在里面用IEEE格式给出一篇完整的论文。我希望你分步、仔细考虑这个问题。这不是让你代替我完成，而是你作为claude code会如何尽全力地给这个项目做出一份汇报。我希望你给我帮助，这最终目的是促进我自己的思考。请尽力完成这个事情，体现你的深度和专业性。


### 20260314

现在我们要做一点git版本管理和数据整理的工作。`verification` and `human-notes`这两个文件夹直接无视。

重新计算`annotated`的数据的SHA。**直接在对话中先完成institution的数据处理，生成图表，然后再做后面的处理。**

更新`output/preparation/DATA_AND_METRICS.md` 和 `output/preparation/data_interpretation.md`. `output/preparation`这个文件夹里面的内容是给我自己看的。

我希望你把`script`里的脚本按照功能都整理一下。比如scrape功能的文件都放在`script/scrape`这个文件夹下。别让我看见零散的东西。这可能涉及到路径的修改。接下来，修改`README.md`. 现在我希望你在`analysis`, `data`, `output`, `scripts` 这几个文件夹下分别建立md文档，记录这个文件夹中每个文件的作用。原来的`README.md`把文件说明相关的信息都删掉。

重写`output/finding_summary.md`. 言简意赅，这个是给读论文的大家看的。

根据我们最新的讨论结果，更新`paper/draft/dft.tex`.

这是我们最后一次动data了，可以打一个小的v更新。