@echo off
git add .gitignore RELEASE_NOTES.md
git commit -m "chore: remove .agents dir, add RELEASE_NOTES, clean gitignore"
git push origin main
echo Done!
