

from ai_feedback import get_ai_feedback


from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "quiz_secret_key"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="himans2601",   # use your actual password
    database="quiz_db1"
)

cursor = db.cursor(dictionary=True)

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def do_login():
    username = request.form['username']
    password = request.form['password']

    query = "SELECT * FROM users WHERE username=%s AND password=%s"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()

    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']   # ✅ ADD THIS
        session['role'] = user['role']


        if user['role'] == 'admin':
            return redirect("/admin")
        else:
            return redirect("/quiz")
    else:
        return "Invalid Username or Password"

@app.route("/admin")
def admin():
    if 'role' in session and session['role'] == 'admin':
        return render_template("admin.html")
    return redirect("/")

@app.route("/quiz")
def quiz():
    if 'role' not in session or session['role'] != 'student':
        return redirect("/")

    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    return render_template("quiz.html", questions=questions)

@app.route("/add_question", methods=["GET", "POST"])
def add_question():
    if 'role' not in session or session['role'] != 'admin':
        return redirect("/")

    if request.method == "POST":
        q = request.form['question']
        o1 = request.form['option1']
        o2 = request.form['option2']
        o3 = request.form['option3']
        o4 = request.form['option4']
        correct = request.form['correct']

        cursor.execute(
            "INSERT INTO questions (question, option1, option2, option3, option4, correct_option) VALUES (%s,%s,%s,%s,%s,%s)",
            (q, o1, o2, o3, o4, correct)
        )
        db.commit()

        return redirect("/admin")

    return render_template("add_question.html")

@app.route("/reset_quiz")
def reset_quiz():
    if 'role' not in session or session['role'] != 'admin':
        return redirect("/")

    cursor.execute("DELETE FROM questions")
    cursor.execute("DELETE FROM results")
    db.commit()

    return redirect("/admin")



@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()

    score = 0
    total_questions = len(questions)
    results = []

    for q in questions:
        # 1. Get user input (This comes as a string, e.g., "1")
        selected = request.form.get(f"q{q['id']}")

        # 2. Convert database value to string for comparison
        correct_opt_num = str(q['correct_option']) 

        # 3. Map the number (1, 2, etc.) to the actual option text
        # Assumes your DB columns are named 'option1', 'option2', etc.
        actual_correct_text = q.get(f"option{correct_opt_num}")
        actual_selected_text = q.get(f"option{selected}") if selected else "No answer"

        if selected == correct_opt_num:
            score += 1
            feedback = "Correct answer. Good understanding."
        else:
            feedback = get_ai_feedback(
                q['question'],
                actual_selected_text,
                actual_correct_text
            )

        results.append({
            "question": q['question'],
            "your_answer": actual_selected_text,      # Shows text, not number
            "correct_answer": actual_correct_text,    # Shows text, not number
            "feedback": feedback
        })

    # Save to database
    cursor.execute(
        "INSERT INTO results (user_id, score, total) VALUES (%s, %s, %s)",
        (session['user_id'], score, total_questions)
    )
    db.commit()

    return render_template(
        "result.html",
        score=score,
        total=total_questions,
        results=results
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)

