@echo off
cd /d "c:\Users\Chris\Desktop\Project_Talos_v4.8.1_GitHub"
python -c "import sys; lines=open('sources/springer_source.py','r',encoding='utf-8').readlines(); lines=[l for i,l in enumerate(lines) if not (36<=i<=43)]; open('sources/springer_source.py','w',encoding='utf-8').writelines(lines); print('FIXED',len(lines))"
python -m py_compile sources/springer_source.py
echo Done
