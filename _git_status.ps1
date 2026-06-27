Set-Location "c:\Users\Chris\Desktop\Project_Talos_v4.8.1_GitHub"
git status > _git_out.txt
git log -1 --name-status >> _git_out.txt
git diff --name-only origin/main >> _git_out.txt
Get-Content _git_out.txt
