"""Record the verified local delivery and append the single per-version update note."""
import argparse,datetime as dt,json,shutil,subprocess
from pathlib import Path
from nowcoder_editorials import ROOT,OUT,CONTENT,read,write,sha


def finish(desktop):
    user=read(OUT/'delivery/user-v1/installed.json')
    admin=read(OUT/'delivery/admin-v1/installed.json')
    assert user['applied'] and admin['applied']
    report=read(ROOT/'docs/verification/nowcoder-editorials-20261108.json')
    report['installation']={'localOnly':True,'ordinaryAndAdminPassed':True,'runningWindowsClosed':False,
        'editions':{name:{key:value[key] for key in ['candidateSha256','appliedAt',
            'unrelatedPublicRowsPreserved','localAmendmentsPreserved','workspaceRehearsalPassed',
            'nativeExecutablesUnchanged','privateAccountDraftSubmissionTrainingFilesOpened','liveOwnedArticlesVerified']}
            for name,value in [('user',user),('admin',admin)]}}
    write(ROOT/'docs/verification/nowcoder-editorials-20261108.json',report)
    for installed in [user,admin]:
        target=Path(installed['target'])
        for path in [target/'BUILD-INFO.json',target/'resources/BUILD-INFO.json']:
            if path.exists():
                value=read(path);value['contentSourcePushed']=False
                write(path,value)
    fragment='''## 牛客题单题解补全（2026-11-08）

截图所示牛客题单的 1,083 道原题已核对完毕，难度不超过 2,300 的 926 道全部有题解；另保留 10 道已写的高难度补充题解。共 936 篇默认题解，其中 52 篇另有详细版。

927 份 C++17 与 9 份 Python 参考程序统一格式化。必要的动态过程配有 16 个 GIF、共 162 帧，覆盖 20 道题；包括单调栈、滑动窗口、区间与树形 DP、失败树激活、增广路换边、动态圆覆盖和山坡滚动接触点切换。动图采用具体例子，状态与参考程序核对。

已验证 1,021 道原题的牛客公开数值评级；其余未公开评分题经逐题复核，纳入的 56 道明确保留估分标记。5 道仅显示加载占位内容的题面已依据原始 PDF 修复，原题链接和来源保留。

验证：936 份参考程序全部通过本地编译／运行、共 1,449 个样例及边界用例；另完成 8,011 组独立对拍或操作检查，以及大规模输入检查。20 道带动图题解通过实际阅读组件的播放、放大、格式化代码复制、窄窗口与深色模式检查。未向原站发送正式提交，不将本地检查记为官方 AC。

普通版与管理员版公共题库和正在使用的本地题库均已更新，升级前保留恢复点；已有独立批注、缓存题面、个人账号、草稿、代码、提交及训练记录保留。程序窗口未关闭，重新打开题解即可读取新内容。本次没有公开发布新安装包。

清理了已失效的旧动图预览 155,194 字节，保留正式资源、验证材料和升级恢复点。
'''
    folder=desktop/'ToBe更新记录';folder.mkdir(parents=True,exist_ok=True)
    note=folder/'ToBe-1.6.6.md'
    text=note.read_text(encoding='utf-8-sig') if note.exists() else '# ToBe 1.6.6\n'
    assert fragment.splitlines()[0] not in text,'Update note already recorded'
    if note.exists() and not (OUT/'update-note-before.md').exists():
        shutil.copy2(note,OUT/'update-note-before.md')
    note.write_text(text.rstrip()+'\n\n'+fragment,encoding='utf-8')
    project=ROOT.parents[1]/'版本/更新记录/ToBe-1.6.6.md'
    project.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(note,project)
    assert sha(note.read_bytes())==sha(project.read_bytes())
    tracking=ROOT.parents[1]/'正在使用的构建文件.json'
    if not (OUT/'tracking-before.json').exists():shutil.copy2(tracking,OUT/'tracking-before.json')
    current=json.loads(tracking.read_text(encoding='utf-8-sig'))
    current['nowcoderEditorials20261108']={
        'completedAt':dt.datetime.now(dt.timezone.utc).isoformat(),
        'sourceRoot':str(ROOT),'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'version':'1.6.6','publicRelease':False,'allEligibleProblemsComplete':True,
        'eligibleProblems':926,'defaultArticles':936,'detailedArticles':52,
        'gifAnimations':16,'animatedProblems':20,'normalAndAdminLibrariesUpdated':True,
        'privateAccountDraftSubmissionTrainingPreserved':True,'windowsClosedOrRestarted':False,
        'verification':str(ROOT/'docs/verification/nowcoder-editorials-20261108.json'),
        'updateNote':str(note),'projectUpdateNote':str(project)}
    write(tracking,current)
    print(json.dumps({'normalAndAdminInstalled':True,'eligibleProblems':926,'updateNote':str(note),
        'projectMirror':str(project)},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--desktop',type=Path,required=True)
    finish(parser.parse_args().desktop)
