git reset origin/main --hard
git fetch
git pull

rm *.joblib
rm model_version.txt
echo "Done..."
echo "Run python3 moderation_model.py, to initialize!"