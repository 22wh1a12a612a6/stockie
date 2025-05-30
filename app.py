from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
import pandas as pd
import feedparser

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Create users database if not exists
if not os.path.exists('users.db'):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE users (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid Credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template('signup.html', error="Passwords do not match")

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=?', (username,))
        if c.fetchone():
            conn.close()
            return render_template('login.html', error="Username already exists")

        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/analysis')
def analysis():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('analysis.html')

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            df = pd.read_csv(file)

            # Simulate predictions
            df['Signal'] = df['Close'].diff().apply(lambda x: 'Bullish' if x > 0 else 'Bearish')
            latest_data = df.iloc[-1]

            return render_template('prediction.html',
                                   close=latest_data['Close'],
                                   prev_close=df.iloc[-2]['Close'],
                                   open_price=latest_data['Open'],
                                   low=df['Low'].min(),
                                   high=df['High'].max(),
                                   week52_low=df['Low'].min(),
                                   week52_high=df['High'].max(),
                                   prediction_low=latest_data['Close'] * 0.98,
                                   prediction_high=latest_data['Close'] * 1.02,
                                   reversal=latest_data['Close'] * 0.99,
                                   accuracy=92,
                                   df=df.to_dict(orient='records'))

    return render_template('prediction.html')

@app.route('/market_news')
def market_news():
    if 'username' not in session:
        return redirect(url_for('login'))

    # RSS feed from Economic Times Markets
    rss_url = 'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms'
    feed = feedparser.parse(rss_url)
    news_items = []

    for entry in feed.entries[:10]:  # Top 10 news
        news_items.append({
            'title': entry.title,
            'url': entry.link,
            'summary': entry.summary,
            'published': entry.published
        })

    return render_template('market_news.html', news=news_items)

@app.route('/chatbot')
def chatbot():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chatbot.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
