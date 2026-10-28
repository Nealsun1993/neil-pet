#!/usr/bin/env python3
"""Package already approved character assets; does not generate images or infer approvals."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

STYLES = {'P01':'粗线彩色卡通','P02':'蜡笔绘本','P03':'轻水彩','P04':'纸片拼贴','P05':'极简墨线','P06':'针毡玩偶'}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def text(value):
    return isinstance(value, str) and bool(value.strip())

def build(brief_path, output, check_only=False):
    brief_path = Path(brief_path).resolve()
    b = json.loads(brief_path.read_text())
    slug = b.get('slug', '')
    require(isinstance(slug, str) and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug) and len(slug) < 64, 'Invalid slug')
    for key in ('name', 'species'):
        require(text(b.get(key)), f'Missing {key}')
    require(b.get('style_id') in STYLES, 'Choose P01–P06')
    require(b.get('release') in ('draft', 'ready'), 'release must be draft or ready')
    for key in ('identity_facts','design_decisions','unknowns','style_rules'):
        require(isinstance(b.get(key), list) and b[key] and all(text(x) for x in b[key]), f'Missing list {key}')
    approvals = b.get('confirmations', {})
    require(isinstance(approvals, dict) and text(approvals.get('hero')), 'Confirmed hero required; unconfirmed trials are not a personal skill')
    assets = b.get('assets', [])
    require(isinstance(assets, list) and assets, 'No assets')
    ids, prepared = set(), []
    for a in assets:
        aid = a.get('id', '')
        require(isinstance(aid,str) and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', aid) and aid not in ids, 'Invalid or duplicate asset id')
        ids.add(aid)
        require(a.get('role') in ('hero','view','expressions','action'), 'Invalid asset role')
        require(a.get('status') in ('confirmed','design-completion'), 'Invalid asset status')
        require(text(a.get('note')), 'Each asset needs evidence/limitations note')
        require(a['status'] == 'confirmed' or a['role'] in ('view','action'), 'Hero and expressions must be confirmed')
        src = Path(a['source'])
        src = (brief_path.parent / src).resolve() if not src.is_absolute() else src.resolve()
        require(src.is_file() and src.suffix.lower() in ('.png','.jpg','.jpeg','.webp'), f'Missing image {aid}')
        # Verify content, not just an image filename. No raw private HEIC files are copied.
        with src.open('rb') as f:
            header = f.read(12)
        require(header.startswith(b'\x89PNG\r\n\x1a\n') or header.startswith(b'\xff\xd8\xff') or (header[:4] == b'RIFF' and header[8:12] == b'WEBP'), f'Invalid image signature {aid}')
        prepared.append((a,src))
    require(sum(a['role']=='hero' for a,_ in prepared)==1, 'Exactly one hero required')
    tests = b.get('application_tests', [])
    require(isinstance(tests,list), 'application_tests must be a list')
    for t in tests:
        require(t.get('type') in ('illustration','article','ppt') and t.get('result') in ('passed','partial') and text(t.get('evidence')) and isinstance(t.get('limitations'),str), 'Invalid test record')
    if b['release']=='ready':
        require(all(text(approvals.get(k)) for k in ('expressions','views')), 'Expression and view approval required')
        require(any(a['role']=='expressions' for a,_ in prepared), 'Expression asset required')
        required={'front','three-quarter-left','three-quarter-right','profile-left','profile-right','rear'}
        require(required <= {a['id'] for a,_ in prepared if a['role']=='view'}, 'Six named views required for ready')
        require(any(t['result']=='passed' for t in tests), 'At least one completed application test required')
    output = Path(output).resolve()
    dest, archive = output/slug, output/(slug+'.zip')
    require(not dest.exists() and not archive.exists(), 'Destination already exists; use a new version folder')
    if check_only:
        return {'valid':True,'release':b['release'],'assets':len(prepared),'written':False}
    output.mkdir(parents=True, exist_ok=True)
    # Stage the entire directory before placing it in the output location.
    with tempfile.TemporaryDirectory(prefix='pet-skill-',dir=output) as tmp:
        root=Path(tmp)/slug
        for folder in ('references','agents','assets/character'):
            (root/folder).mkdir(parents=True,exist_ok=True)
        manifest=[]
        for a,src in prepared:
            rel='assets/character/'+a['id']+src.suffix.lower()
            shutil.copyfile(src,root/rel)
            manifest.append({k:a[k] for k in ('id','role','status','note')} | {'path':rel,'sha256':hashlib.sha256((root/rel).read_bytes()).hexdigest()})
        record={k:b[k] for k in ('name','species','style_id','release','identity_facts','design_decisions','unknowns','style_rules','confirmations')}
        record['application_tests']=tests
        record['style_name']=STYLES[b['style_id']]
        (root/'references/character.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
        (root/'assets/character/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        # JSON scalar strings are valid YAML quoted scalars.
        q=lambda s: json.dumps(s,ensure_ascii=False)
        desc=f'沿用已确认宠物 {b["name"]} 的专属形象制作插画、生图设计或可编辑 PPT；仅在用户点名该角色时使用。'
        entry=f'''---
name: {slug}
description: {q(desc)}
---

# {b['name']} · 专属宠物创作

先读 [角色档案](references/character.json) 和 [资产清单](assets/character/manifest.json)，查看主形象与匹配机位参考，再读 [创作规则](references/creation.md)。本包等级为 {b['release']}，画风为 {STYLES[b['style_id']]}。

只沿用本角色，不从其他同名动物或母包案例补身份。照片事实、设计决定、未知和用户确认以角色档案为准。主参考优先，动作图与场景不能反向覆盖身份。已有参考的日常创作无需重新交照片；缺失角度补照片或取得明确创作补全选择。draft 的缺项不称为完成。

按任务读取实际可用的图像或演示工具要求。工具不足时说明只完成到提示词／排版阶段，不冒称成图或 PPTX。调用示例：“用 ${slug}，根据这篇正文设计宠物插画。”
'''
        (root/'SKILL.md').write_text(entry)
        # Embed adapted application guidance so child has no mother-skill dependency.
        common=(Path(__file__).resolve().parent.parent/'references/applications.md').read_text()
        (root/'references/creation.md').write_text('''# 个人角色创作约束

使用角色档案中的 style_rules 和身份，不继承任何测试案例的颜色、材质或比例。默认自然友好，表情以本包确认板为准，专注不画成生气，放松不画成不悦。宠物爪形遵循确认设定，防止多肢、人类手指、断开的尾巴、道具穿插。

按机位选择单张参考，必要时加主参考；不把所有角度一起塞进同次构图。花纹不擅自镜像。references/character.json 中未知及补全声明需要保留。新图后检查身份、情绪、解剖与材质，透明素材检查实际 alpha。

以下是可用的设计方法，实际验证范围仅以 application_tests 为准；无记录即待验证。动画未纳入。

'''+common)
        (root/'agents/openai.yaml').write_text('interface:\n  display_name: '+q(b['name']+' · 宠物创作')+'\n  short_description: '+q('沿用这只宠物已确认的角色参考，完成主题插画、生图设计和可编辑演示文稿')+'\n  default_prompt: '+q('使用 $'+slug+'，沿用我的宠物角色完成本次创作。')+'\n')
        # Keep method attribution with the portable child.
        shutil.copyfile(Path(__file__).resolve().parent.parent/'references/sources.md',root/'references/method-sources.md')
        with (root/'references/creation.md').open('a') as f:
            f.write('\n方法出处与适配边界见 [来源](method-sources.md)。来源中的 Tom 验证历史不代表本角色已完成同样测试。\n')
        tmp_zip=Path(tmp)/(slug+'.zip')
        with zipfile.ZipFile(tmp_zip,'w',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(root.rglob('*')):
                if p.is_file(): z.write(p,str(Path(slug)/p.relative_to(root)))
        shutil.move(str(root),dest)
        shutil.move(str(tmp_zip),archive)
    return {'valid':True,'release':b['release'],'assets':len(prepared),'directory':str(dest),'zip':str(archive)}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--brief',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args()
    try:
        print(json.dumps(build(args.brief,args.output,args.check_only),ensure_ascii=False))
    except (ValueError,KeyError,TypeError,OSError) as e:
        parser.exit(2,'Cannot package: '+str(e)+'\n')
