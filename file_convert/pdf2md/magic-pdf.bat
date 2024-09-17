@echo off
:: 设置需要读取的目录
set "target_file=os_test.pdf"

:: 输出目录中的所有文件
@REM echo Processing files in directory: %targetDirectory%

magic-pdf -p "%target_file%" -o md

echo All files processed successfully.

endlocal
pause
exit /b 0