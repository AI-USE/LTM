from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route("/")
def home():
    return {"message": "Render Flask App is running!"}

@app.route("/scrape", methods=["GET"])
def scrape():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "url パラメータを指定してください"}), 400

    try:
        # ページ取得
        html = requests.get(url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        # タイトル取得
        title_tag = soup.find("title")
        if not title_tag:
            return jsonify({"error": "タイトルが取得できません"}), 500

        title = title_tag.text.strip()

        # タイトル形式チェック [曲名 歌詞 作者 ふりがな付 - うたてん]
        if "歌詞" not in title or "ふりがな付" not in title:
            return jsonify({"error": "対応していないタイトル形式です"}), 400

        try:
            song = title.split("歌詞")[0].strip()
            author = title.split("歌詞")[1].split("ふりがな付")[0].strip()
        except Exception as e:
            return jsonify({"error": f"解析に失敗しました: {e}"}), 500

        return {
            "song": song,
            "author": author,
            "title_raw": title
        }

    except Exception as e:
        return jsonify({"error": f"接続エラー: {e}"}), 500


if __name__ == "__main__":
    # Render 用: 0.0.0.0 で待ち受け
    app.run(host="0.0.0.0", port=5000)
