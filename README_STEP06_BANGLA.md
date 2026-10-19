# Step 6 — Streamlit Chatbot UI এবং GitHub Submission

আপনার আগের Step 1–5-এর code ও `.env` একই থাকবে। এই ZIP শুধুমাত্র নতুন Step 6 files এবং প্রয়োজনীয় updated root documentation যোগ করবে।

## File placement

`D:\Multi_Tool_AI_Agent_Bangladesh` project folder-এ ZIP extract করে **merge** করুন।

- `app.py`: নতুন Streamlit chatbot; Step 1-এর খালি placeholder `app.py` থাকলে replace করুন।
- `ui_helpers.py`: chat history, safe source URL, friendly error এবং আসল DB row counter।
- `tests/test_step06_ui_helpers.py`: ৮টি offline tests।
- `README.md`, `requirements.txt`, `.gitignore`, `.env.example`: GitHub submission-ready versions।

**সতর্কতা:** `.env` (আসল keys), তিনটি SQLite database এবং Step 2–5-এর tools/scripts কোনোটি overwrite বা delete করবেন না। ZIP-এ এসব ফাইল নেই।

## Run in VS Code Terminal

```powershell
cd D:\Multi_Tool_AI_Agent_Bangladesh
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q tests/test_step06_ui_helpers.py
python -m streamlit run app.py
```

Browser-এ local Streamlit URL (সাধারণত `http://localhost:8501`) খুলুন।

## UI-তে কী আছে?

1. বাংলা ও English text chat
2. ৪টি Example Question buttons
3. Sidebar-এ SQLite-এর আসল record count (জাতীয় মোট নয়)
4. Agent আসলেই কোন tool ব্যবহার করেছে তা প্রদর্শন
5. Web Search result-এর source URL
6. Session-only conversation history এবং Clear Conversation button
7. Secret প্রকাশ না করে API/network error message

**নোট:** UI চালিয়ে পরীক্ষা না করা পর্যন্ত এটি complete বলে ধরে নেব না। Groq/Tavily live answer free-tier API quota ব্যবহার করতে পারে।

## Suggested demo questions

```
How many institution records are in the provided institutions dataset?
How many health-facility records are in Dhaka district?
Show 5 highly rated food places in Dhaka with at least 20 reviews.
What is the role of DGHS in Bangladesh? Cite a source.
```

Dataset records ≠ অফিসিয়াল জাতীয় সংখ্যা। Hospital rows-এ অন্য ধরনের health offices-ও আছে; restaurants source-এ non-restaurant rows-ও আছে।

## GitHub Submission

আপনার screenshot demo নেওয়ার পর:

```powershell
git init
git add .
git status
```

**`git status` পরীক্ষা করুন:** `.env`, `.venv`, downloaded raw datasets, generated `.db` যেন stage না হয়। `.gitignore` এদের বাদ দেয়।

```powershell
git commit -m "Complete Bangladesh Multi-Tool AI Agent assignment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

GitHub-এ আগে একটি empty repo তৈরি করতে হবে। `YOUR_USERNAME` এবং `YOUR_REPO` নিজের তথ্য দিয়ে বদলান। Existing Git remote থাকলে `git remote -v` দেখে তারপর command দিন।

**Submission:** GitHub repository URL + local app screenshot। চাইলে optional Colab demo আলাদাভাবে দেওয়া যাবে।
