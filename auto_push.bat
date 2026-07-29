@echo off
cd /d C:\Users\Administrator\Desktop\sunset-web
git add index.html
git commit -m "Auto update sunset forecast at %date% %time%"
git push origin main