@echo off
chcp 65001 >nul
title 群聊报告更新工具

echo.
echo    🌲  群聊分析报告 — 一键更新
echo    ═══════════════════════════════
echo.
echo    把聊天记录 messages.txt 放到这个文件夹里
echo    然后按任意键继续...
pause >nul

if not exist "messages.txt" (
    echo.
    echo    ❌ 没找到 messages.txt！
    echo    请先把留痕导出的文件改名为 messages.txt
    echo    放到这个文件夹，再重新运行我。
    echo.
    pause
    exit
)

echo    📊 正在上传到 GitHub...

git add messages.txt
git commit -m "更新聊天记录 %date%"
git push

echo.
echo    ✅ 更新完成！
echo    等 1-2 分钟后打开：
echo    https://g-d572.github.io/wechat-report/
echo.
pause
