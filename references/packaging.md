# 从定制母 Skill 产出个人包

## 独立结构

每只宠物使用唯一 slug，如 `momo-pet-studio`。交付目录包含 SKILL.md、agents/openai.yaml、references/character.json、references/creation.md、assets/character/manifest.json 和必要角色图。生成的个人包无需安装本母包；只需目标环境具备实际图像／演示工具。大体积案例单独交付，不默认携带私人照片、其他宠物或测试作者素材。

## 使用打包器

准备 UTF-8 JSON，按 `assets/brief-example.json` 的字段填写。该例只有虚构结构，无真实形象，不能直接定稿。

运行：`python3 scripts/build_personal_skill.py --brief 角色档案.json --output 用户交付目录`

输出目录必须尚无同名包及 ZIP，避免覆盖。可先用 `--check-only` 核对；脚本不调用图像生成、不安装或修改其他 Skill、不上传数据。资产 source 的相对路径按 brief 所在文件夹解析；打包后只保留包内相对路径和哈希。

字段：
- slug：小写字母数字短横线，使用 `<名字>-pet-studio`。
- name、species、style_id：宠物名字、用户确认的种类描述、P01–P06。
- identity_facts、design_decisions、unknowns、style_rules：非空列表，未知项可写“无额外信息”。照片事实不写本机路径或私人个人信息。
- confirmations：hero、expressions、views 三个非空字符串，写实际确认依据。未确认不得伪造填写。
- assets：每项 id、role、source、status、note。role 为 hero、view、expressions 或 action；status 为 confirmed 或 design-completion；只有 view/action 可用 design-completion，并在 note 写用户授权及补全部位。id 用可辨识英文短横线，view 包括角度含义。
- application_tests：每项 type（illustration/article/ppt）、result（passed/partial）、evidence（交付文件名或可复核说明）、limitations。这里只登记实际完成的测试；大案例不复制进角色包。
- release：draft 或 ready。ready 需主形象、表情、六角度及至少一项 passed 应用测试；draft 只需确认主形象，其余缺项会保留为未完成。发布等级是本包设计完整度，不表示公共发布或全部工具环境已兼容。

脚本只做材料和结构校验，不能判断图像质量、用户确认真伪或引用事实；执行者必须查看图并核对会话。没有必要为了打包强行新增未请求的图或测试，可交清楚标注的 draft。

## 验收与交付

运行环境提供的 skill-creator 校验器；检查所有相对引用、哈希与 ZIP 内容可读，确认个人包不依赖作者绝对路径。审阅身份记录及确认依据。透明素材另检真实 alpha；PPT 另做实际渲染／原生对象验证。对用户说明本版本可用能力、局限、调用句和安装方法。默认先交目录和 ZIP；只有用户要求本机安装时再安装个人包。
